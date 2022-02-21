# -*- coding: utf-8 -*-
"""Node terminate command tests."""

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

from click.testing import CliRunner

from metamorphctl.cli import Environment
from metamorphctl.commands.node_terminate_command import cli


@patch('boto3.client')
@patch('metamorphctl.commands.node_terminate_command.find_ec2_instance')
def test_node_terminate_not_found(find_ec2_instance_mock, boto_mock):
    """Test node terminate when no ec2 instancer has been found."""
    runner = CliRunner()
    find_ec2_instance_mock.return_value = None
    runner.invoke(cli, '-n node')
    boto_mock.assert_not_called()


@patch('boto3.client')
@patch('metamorphctl.commands.node_terminate_command.find_ec2_instance')
def test_no_terminate_node_without_confirmation(find_ec2_instance_mock, boto_mock):
    """Test should not terminate node without confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False
    find_ec2_instance_mock.return_value = {'InstanceId': 'i-123456', 'Tags': []}

    res = runner.invoke(cli, '-n node', obj=env)

    assert res.exit_code != 0, res.output
    boto_mock.assert_not_called()


@patch('boto3.client')
@patch('metamorphctl.commands.node_terminate_command.find_ec2_instance')
def test_terminate_node_with_confirmation(find_ec2_instance_mock, boto_mock):
    """Test terminate node with confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    instance_id = 'i-123456'
    find_ec2_instance_mock.return_value = {'InstanceId': instance_id, 'Tags': []}
    ec2_mock = MagicMock()
    boto_mock.return_value = ec2_mock

    res = runner.invoke(cli, '-n node', obj=env)

    assert res.exit_code == 0, res.output
    ec2_mock.terminate_instances.assert_called_with(InstanceIds=[instance_id])


@patch('boto3.client')
@patch('metamorphctl.commands.node_terminate_command.find_ec2_instance')
def test_terminate_node_raises_exception(find_ec2_instance_mock, boto_mock):
    """Test raise on exception."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    find_ec2_instance_mock.return_value = {'InstanceId': 'i-123456', 'Tags': []}
    boto_mock.side_effect = Exception()

    res = runner.invoke(cli, '-n node', obj=env)

    assert isinstance(res.exception, Exception)
    boto_mock.assert_called()
