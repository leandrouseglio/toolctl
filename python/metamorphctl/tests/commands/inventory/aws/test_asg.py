# -*- coding: utf-8 -*-
"""Asg unit tests."""

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
from metamorphctl.commands.inventory.aws_handlers.asg import Asg


def test_handle():
    """Test if handle method works as expected."""
    with mock.patch("boto3.client") as mocked_client:
        expected = "test"
        mocked_client.return_value.describe_auto_scaling_groups.return_value = {
            "AutoScalingGroups": [{
                "Expected": expected,
                "AutoScalingGroupARN": "testarn"
            }]
        }

        target = Asg("test")
        actual = target.handle()
        assert len(actual) == 1
        assert actual[0]["Expected"] == expected
