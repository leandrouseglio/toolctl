# -*- coding: utf-8 -*-
"""Handler."""

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

import boto3


class Iam():
    """Collect IAM items."""

    def __init__(self, kernel_ns):
        """Init."""
        self.kernel_ns = kernel_ns
        self.client = boto3.client("iam")

    def handle(self):
        """Handle collection of items."""
        return {
            "Roles": self._handle_items(self.client.list_roles, "Roles"),
            "Policies": self._handle_items(self.client.list_policies, "Policies")
        }

    def _handle_items(self, func, category):
        res = []
        marker = None
        while True:
            resp = func(MaxItems=100) if not marker \
                else func(Marker=marker, MaxItems=100)
            res += [
                ro for ro in resp[category] if self.kernel_ns in ro["Arn"]
            ]
            marker = resp["Marker"] if resp.get("IsTruncated", False) else None
            if not marker:
                break
        return res
