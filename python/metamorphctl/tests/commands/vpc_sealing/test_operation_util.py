# -*- coding: utf-8 -*-
"""Operation util tests."""

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

from mock import patch
import pytest
from jsonschema import ValidationError
from metamorphctl.commands.vpc_sealing.operation_util import OperationUtil
from metamorphctl.commands.vpc_sealing.operation_util import DEFAULT_RULE_NUMBER


@pytest.fixture
def boto3_mock():
    """Initialize boto3 mock."""
    patcher = patch("boto3.client")
    mocked_client = patcher.start()
    mocked_client.return_value.describe_network_acls.return_value = {
        "NetworkAcls": [{
            "NetworkAclId": "test",
            "Entries": [{
                "CidrBlock": "0.0.0.0/0"
            }]
        }]
    }
    yield mocked_client
    patcher.stop()


@pytest.fixture
def boto3_resource_mock():
    """Initialize boto3 resource mock."""
    patcher = patch("boto3.resource")
    mocked_resource = patcher.start()
    mocked_resource.return_value.Vpc.return_value.cidr_block = "10.0.0.0/16"
    yield mocked_resource
    patcher.stop()


# pylint: disable=unused-argument, redefined-outer-name


def test_get_nacl_entries(boto3_mock):
    """Test if method works properly."""
    target = OperationUtil("test")
    actual = target.get_nacl_entries()
    assert len(actual) == 1
    assert actual[0]["CidrBlock"] is not None


def test_remove_nacl_entry(boto3_mock):
    """Test if method works properly."""
    boto3_mock.return_value.delete_network_acl_entry.return_value = {}
    entry = {"RuleNumber": 1, "Egress": True}

    target = OperationUtil("test")
    target.remove_nacl_entry(entry)
    boto3_mock.return_value.delete_network_acl_entry.assert_called()


def test_do_not_remove_nacl_entry_if_default(boto3_mock):
    """Test if method works properly."""
    boto3_mock.return_value.delete_network_acl_entry.return_value = {}
    entry = {"RuleNumber": DEFAULT_RULE_NUMBER, "Egress": True}

    target = OperationUtil("test")
    target.remove_nacl_entry(entry)
    boto3_mock.return_value.delete_network_acl_entry.assert_not_called()


def test_add_nacl_entry(boto3_mock):
    """Test if method works properly."""
    boto3_mock.return_value.create_network_acl_entry.return_value = {}
    entry = {"CidrBlock": "0.0.0.0/0", "RuleNumber": 1, "Egress": True, "RuleAction": "allow"}

    target = OperationUtil("test")
    target.add_nacl_entry(entry)
    boto3_mock.return_value.create_network_acl_entry.assert_called()


def test_replace_nacl_entries_empty_entries(boto3_mock):
    """Test if method works properly."""
    boto3_mock.return_value.delete_network_acl_entry.return_value = {}
    boto3_mock.return_value.create_network_acl_entry.return_value = {}
    entries = []

    target = OperationUtil("test")
    with pytest.raises(ValueError):
        target.replace_nacl_entries(entries, "allow")

    boto3_mock.return_value.delete_network_acl_entry.assert_not_called()
    boto3_mock.return_value.create_network_acl_entry.assert_not_called()


def test_replace_nacl_entries_invalid_cidr(boto3_mock):
    """Test if method works properly."""
    boto3_mock.return_value.delete_network_acl_entry.return_value = {}
    boto3_mock.return_value.create_network_acl_entry.return_value = {}
    entries = [{"Egress": True, "CidrBlock": "192.168.0.1/33"}]

    target = OperationUtil("test")
    with pytest.raises(ValidationError):
        target.replace_nacl_entries(entries, "allow")

    boto3_mock.return_value.delete_network_acl_entry.assert_not_called()
    boto3_mock.return_value.create_network_acl_entry.assert_not_called()


def test_replace_nacl_entries(boto3_mock):
    """Test if method works properly."""
    # current entries
    boto3_mock.return_value.describe_network_acls.return_value = {
        "NetworkAcls": [{
            "NetworkAclId": "test",
            "Entries": [{
                "CidrBlock": "0.0.0.0/0",
                "RuleNumber": 1,
                "Egress": True
            }]
        }]
    }
    boto3_mock.return_value.delete_network_acl_entry.return_value = {}
    boto3_mock.return_value.create_network_acl_entry.return_value = {}
    entries = [
        {
            "CidrBlock": "0.0.0.0/0",
            "RuleNumber": 1,
            "Egress": False
        },
    ]

    target = OperationUtil("test")
    target.replace_nacl_entries(entries, "allow")

    boto3_mock.return_value.delete_network_acl_entry.assert_called()
    boto3_mock.return_value.create_network_acl_entry.assert_called()


def test_describe_operation(boto3_mock, boto3_resource_mock):
    """Test if method works properly."""
    expected = "test-operation"
    actual = OperationUtil("test").describe_operation(expected, [{
        "Egress": True,
        "CidrBlock": "0.0.0.0/0"
    }], True)
    assert actual is not None
    assert expected.upper() in actual
