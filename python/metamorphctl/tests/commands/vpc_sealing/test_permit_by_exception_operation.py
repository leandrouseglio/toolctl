# -*- coding: utf-8 -*-
"""Permit by exception operation tests."""

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

from unittest.mock import Mock, patch
from metamorphctl.commands.vpc_sealing.permit_by_exception_operation \
    import PermitByExceptionOperation
from metamorphctl.utils.config import Config


@patch.object(Config, "__init__", lambda x: None)
@patch.object(Config, "get")
def test_describe_with_no_rule_matching_vpc_cidr(mocked_get):
    """Test if method works properly."""

    expected = [{"Egress": True, "CidrBlock": "0.0.0.0/0"}]
    mocked_get.return_value = {"whitelist": expected}
    attrs = {"describe_operation.return_value": "test", "get_vpc_cidr.return_value": "10.0.0.0/16"}
    util = Mock(**attrs)

    target = PermitByExceptionOperation(util)
    actual = target.describe()

    assert actual is not None
    util.describe_operation.assert_called()

    # check requested input parameter, it should contain:
    # - 2 rules for vpc_cidr (egress & ingress)
    # - 1 rule for the configured CIDR
    assert util.describe_operation.call_args_list == [({
        "name":
        "permit-by-exception",
        "whitelist":
        True,
        "requested": [{
            'Egress': True,
            'CidrBlock': '0.0.0.0/0'
        }, {
            'Egress': False,
            'CidrBlock': '10.0.0.0/16'
        }, {
            'Egress': True,
            'CidrBlock': '10.0.0.0/16'
        }]
    }, )]


@patch.object(Config, "__init__", lambda x: None)
@patch.object(Config, "get")
def test_describe_with_rule_matching_vpc_cidr(mocked_get):
    """Test if method works properly."""

    expected = [{"Egress": True, "CidrBlock": "10.0.0.0/16"}]
    mocked_get.return_value = {"whitelist": expected}
    attrs = {"describe_operation.return_value": "test", "get_vpc_cidr.return_value": "10.0.0.0/16"}
    util = Mock(**attrs)

    target = PermitByExceptionOperation(util)
    actual = target.describe()

    assert actual is not None
    util.describe_operation.assert_called()

    # check requested input parameter, it should contain:
    # - 2 rules for vpc_cidr (egress & ingress)
    assert util.describe_operation.call_args_list == [({
        "name":
        "permit-by-exception",
        "whitelist":
        True,
        "requested": [{
            'Egress': True,
            'CidrBlock': '10.0.0.0/16'
        }, {
            'Egress': False,
            'CidrBlock': '10.0.0.0/16'
        }]
    }, )]


@patch.object(Config, "__init__", lambda x: None)
@patch.object(Config, "get")
def test_apply(mocked_get):  # pylint: disable=unused-argument
    """Test if method works properly."""

    attrs = {"replace_nacl_entries.return_value": None}
    util = Mock(**attrs)

    target = PermitByExceptionOperation(util)
    target.apply()

    util.replace_nacl_entries.assert_called()
