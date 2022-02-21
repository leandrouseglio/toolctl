# -*- coding: utf-8 -*-
"""Operation util."""

# MCAFEE CONFIDENTIAL
# Copyright © 2019 McAfee LLC.
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by McAfee Corporation or its suppliers
# or licensors. Title to the Material remains with McAfee Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of McAfee or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or
# disclosed in any way without McAfee's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be
# express and approved by McAfee in writing

import json
import boto3
import jsonschema

DEFAULT_RULE_NUMBER = 32767  # AWS DEFAULT RULE NUMBER

NACL_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "Egress": {
            "type": "boolean"
        },
        "CidrBlock": {
            "type": "string",
            "pattern":
            "^([0-9]{1,3}\\.){3}[0-9]{1,3}(\\/([0-9]|[1-2][0-9]|3[0-2]))?$"
        },
        "RuleAction": {
            "type": "string",
            "enum": ["allow", "deny"]
        },
        "RuleNumber": {
            "type": "number"
        }
    },
    "required": ["Egress", "CidrBlock"],
    "additionalProperties": False
}


class OperationUtil():
    """Class to run operations against AWS resources."""

    def __init__(self, vpc_id):
        """Init."""

        self.vpc_id = vpc_id
        self.client = boto3.client("ec2")
        self.vpc_client = boto3.resource("ec2").Vpc(self.vpc_id)
        self.network_acl_id = self.client.describe_network_acls(Filters=[{
            "Name": "default",
            "Values": ["true"]
        }, {
            "Name": "vpc-id",
            "Values": [self.vpc_id]
        }])["NetworkAcls"][0]["NetworkAclId"]

    def get_nacl_entries(self):
        """Get NACL entries."""
        res = []
        token = None
        while True:
            resp = self.client.describe_network_acls(
                MaxResults=100,
                Filters=[
                    {"Name": "default", "Values": ["true"]},
                    {"Name": "network-acl-id", "Values": [self.network_acl_id]}]) if not token \
                else self.client.describe_network_acls(
                    MaxResults=100,
                    Filters=[
                        {"Name": "default", "Values": ["true"]},
                        {"Name": "network-acl-id", "Values": [self.network_acl_id]}],
                    NextToken=token)
            for acls in resp["NetworkAcls"]:
                for entry in acls["Entries"]:
                    res.append(entry)
            token = resp.get("NextToken", None)
            if not token:
                break
        return res

    def remove_nacl_entry(self, entry):
        """Remove NACL entry."""
        if entry["RuleNumber"] != DEFAULT_RULE_NUMBER:
            self.client.delete_network_acl_entry(
                NetworkAclId=self.network_acl_id,
                Egress=entry["Egress"],
                RuleNumber=entry["RuleNumber"],
            )

    def add_nacl_entry(self, entry):
        """Add NACL entry."""
        self.client.create_network_acl_entry(
            NetworkAclId=self.network_acl_id,
            CidrBlock=entry["CidrBlock"],
            Egress=entry["Egress"],
            Protocol="-1",  # hard-coded (all protocols)
            RuleAction=entry["RuleAction"],
            RuleNumber=entry["RuleNumber"])

    def describe_operation(self, name, requested, whitelist=False):
        """Describe the operation."""
        desc = """
#########################
{name}
=========================
This operation will be applied over:
- VPC (ID)={vpc_id}
- VPC Default NACL (ID)={nacl_id}
- VPC CIDR block={cidr_block}
- VPC Tags={tags}
=========================
CURRENT NACL ENTRIES={current}
Entries with RuleNumber=32767 are AWS default ones so CANNOT be added, changed or removed,
the rest will be REMOVED as part of this action.\n
{footer}
#########################
"""
        footer = ""
        if requested:
            self._validate_nacl_entries(requested)
            footer = "{list} TO BE CONFIGURED={requested}".format(
                list=("WHITELIST" if whitelist else "BLACKLIST"), requested=self._format(requested))

        return desc.format(
            name=name.upper(),
            vpc_id=self.vpc_id,
            nacl_id=self.network_acl_id,
            cidr_block=self.get_vpc_cidr(),
            tags=self.vpc_client.tags,
            current=self._format(self.get_nacl_entries()),
            footer=footer)

    def replace_nacl_entries(self, requested_entries, action):
        """Replace NACL entries."""
        try:
            self._validate_nacl_entries(requested_entries)

            # get current entries, then remove then
            current_entries = self.get_nacl_entries()
            print("Current entries={}".format(self._format(current_entries)))
            for entry in current_entries:
                self.remove_nacl_entry(entry)

            # create requested entries
            ingress_entries = [entry for entry in requested_entries if entry["Egress"] is False]
            egress_entries = [entry for entry in requested_entries if entry["Egress"] is True]
            self._create_entries(ingress_entries, action)
            self._create_entries(egress_entries, action)

            print("\nDONE. Entries after modification={}\n".format(
                self._format(self.get_nacl_entries())))
        except Exception as err:  # pylint: disable=broad-except
            print("Exception been caught, error:", err)
            raise err

    def _create_entries(self, requested_entries, action):
        rule_number = 0
        for entry in requested_entries:
            rule_number += 100
            entry["RuleNumber"] = rule_number
            if "RuleAction" not in entry:
                entry["RuleAction"] = action
            self.add_nacl_entry(entry)

    def get_vpc_cidr(self):
        """Return current VPC CIDR block."""
        return self.vpc_client.cidr_block

    @staticmethod
    def _validate_nacl_entries(entries):
        """Validate NACL entries."""
        if not entries:
            raise ValueError("Not provided entries.")
        for entry in entries:
            jsonschema.validate(instance=entry, schema=NACL_ENTRY_SCHEMA)

    @staticmethod
    def _format(content):
        """Format the content to JSON."""
        return json.dumps(content, indent=2)
