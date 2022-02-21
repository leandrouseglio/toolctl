# -*- coding: utf-8 -*-
"""Iam unit tests."""

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

from unittest import mock
from metamorphctl.commands.inventory.aws_handlers.iam import Iam


def test_handle():
    """Test if handle method works as expected."""
    with mock.patch("boto3.client") as mocked_client:
        expected = "test"
        mocked_client.return_value.list_roles.return_value = {
            "Roles": [{
                "Expected": expected,
                "Arn": "testeks"
            }]
        }
        mocked_client.return_value.list_policies.return_value = {
            "Policies": [{
                "Expected": expected,
                "Arn": "testeks"
            }]
        }

        target = Iam("test")
        actual = target.handle()
        assert len(actual) == 2
        assert len(actual["Roles"]) == 1
        assert actual["Roles"][0]["Expected"] == expected
        assert len(actual["Policies"]) == 1
        assert actual["Policies"][0]["Expected"] == expected
