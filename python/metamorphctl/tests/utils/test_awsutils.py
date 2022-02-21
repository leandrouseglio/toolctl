# -*- coding: utf-8 -*-
"""Test aws utils."""

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

from unittest.mock import MagicMock, patch

from metamorphctl.utils.awsutils import find_ec2_instance


@patch('boto3.client')
def test_find_ec2_instance_not_found(boto_mock):
    """Test no result should be returned when ec2 instance is not found."""
    ec2_mock = MagicMock()
    ec2_mock.describe_instances.return_value = {'Reservations': None}
    boto_mock.return_value = ec2_mock

    ec2_instance = find_ec2_instance('foo')

    assert ec2_instance is None


@patch('boto3.client')
def test_find_ec2_instance_by_instance_id(boto_mock):
    """Test result found by instance ip."""
    ec2_mock = MagicMock()
    ec2_mock.describe_instances.side_effect = _by_instance_id
    boto_mock.return_value = ec2_mock

    ec2_instance = find_ec2_instance('foo')

    assert ec2_instance is not None


@patch('boto3.client')
def test_find_ec2_instance_by_private_ip(boto_mock):
    """Test result found by private ip."""
    ec2_mock = MagicMock()
    ec2_mock.describe_instances.side_effect = _by_private_ip
    boto_mock.return_value = ec2_mock

    ec2_instance = find_ec2_instance('foo')

    assert ec2_instance is not None


@patch('boto3.client')
def test_find_ec2_instance_by_private_dns_name(boto_mock):
    """Test result found by private dns name."""
    ec2_mock = MagicMock()
    ec2_mock.describe_instances.side_effect = _by_private_dns
    boto_mock.return_value = ec2_mock

    ec2_instance = find_ec2_instance('foo')

    assert ec2_instance is not None


def _by_instance_id(Filters):  # noqa
    if Filters[0]['Name'] == 'instance-id':
        return {'Reservations': MagicMock()}
    return {'Reservations': None}


def _by_private_ip(Filters):  # noqa
    if Filters[0]['Name'] == 'private-ip-address':
        return {'Reservations': MagicMock()}
    return {'Reservations': None}


def _by_private_dns(Filters):  # noqa
    if Filters[0]['Name'] == 'private-dns-name':
        return {'Reservations': MagicMock()}
    return {'Reservations': None}
