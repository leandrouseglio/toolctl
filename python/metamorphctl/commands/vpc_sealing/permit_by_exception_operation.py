# -*- coding: utf-8 -*-
"""Permit-by-exception Operation."""

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

from metamorphctl.utils.config import Config


class PermitByExceptionOperation():
    """Permit-by-expception implementation."""

    def __init__(self, operation_util):
        """Init."""
        self.util = operation_util
        configured_entries = Config().get("vpc_sealing").get("whitelist")
        configured_entries = self._check_vpc_cidr(configured_entries, False)
        self.requested_entries = self._check_vpc_cidr(configured_entries, True)

    def _check_vpc_cidr(self, entries, egress):
        vpc_cidr = self.util.get_vpc_cidr()
        vpc_entries = [
            entry for entry in entries
            if entry["Egress"] == egress and entry["CidrBlock"] == vpc_cidr
        ]
        if not vpc_entries:
            # not rules for vpc
            entries.append({"Egress": egress, "CidrBlock": vpc_cidr})
        return entries

    def describe(self):
        """Describe what changes will be perfomed by this operation."""

        return self.util.describe_operation(
            name="permit-by-exception", whitelist=True, requested=self.requested_entries)

    def apply(self):
        """Apply the operation."""
        self.util.replace_nacl_entries(self.requested_entries, action="allow")
