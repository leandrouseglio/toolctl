# -*- coding: utf-8 -*-
"""Deny-all Operation."""

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

ENTRIES = [{"Egress": True}, {"Egress": False}]


class DenyAllOperation():
    """Deny-all implementation."""

    def __init__(self, operation_util):
        """Init."""
        self.util = operation_util
        self.requested_entries = []
        for entry in ENTRIES:
            entry["CidrBlock"] = self.util.get_vpc_cidr()
            self.requested_entries.append(entry)

    def describe(self):
        """Describe what changes will be perfomed by this operation."""

        return self.util.describe_operation(
            name="deny-all", whitelist=True, requested=self.requested_entries)

    def apply(self):
        """Apply the operation."""
        self.util.replace_nacl_entries(self.requested_entries, action="allow")
