# -*- coding: utf-8 -*-
"""Node isolate command tests."""

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

from unittest.mock import patch

from click.testing import CliRunner

from metamorphctl.cli import Environment
from metamorphctl.commands.node_isolate_command import cli


@patch('metamorphctl.commands.node_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.node_isolate_command.exist_node', lambda *args: False)
@patch('metamorphctl.commands.node_isolate_command.node_snapshot_command')
def test_isolate_no_node_found(mock_node_snapshot):
    """Test isolate when no node has been found."""
    runner = CliRunner()
    runner.invoke(cli, '-n node')
    mock_node_snapshot.cli.assert_not_called()


@patch('metamorphctl.commands.node_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.node_isolate_command.exist_node', lambda *args: True)
@patch('metamorphctl.commands.node_isolate_command.node_snapshot_command')
def test_no_isolate_node_without_confirmation(mock_node_snapshot):
    """Test should not isolate without confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False

    res = runner.invoke(cli, '-n node', obj=env)

    assert res.exit_code != 0, res.output
    mock_node_snapshot.cli.assert_not_called()


@patch('builtins.input', lambda *args: 'y')
@patch('metamorphctl.commands.node_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.node_isolate_command.exist_node', lambda *args: True)
@patch('metamorphctl.commands.node_isolate_command.node_snapshot_command')
@patch('metamorphctl.commands.node_isolate_command.node_drain_command')
@patch('metamorphctl.commands.node_isolate_command.node_terminate_command')
def test_isolate_node_with_confirmation(mock_terminate, mock_drain, mock_snapshot):
    """Test isolate pods with confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    node = "node123"

    res = runner.invoke(cli, ['-n', node], obj=env)

    assert res.exit_code == 0, res.output
    mock_snapshot.cli.assert_called_with(node=node)
    mock_drain.cli.assert_called_with(node=node)
    mock_terminate.cli.assert_called_with(node=node)


@patch('metamorphctl.commands.node_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.node_isolate_command.exist_node', lambda *args: True)
@patch('metamorphctl.commands.node_isolate_command.node_snapshot_command')
@patch('metamorphctl.commands.node_isolate_command.node_drain_command')
@patch('metamorphctl.commands.node_isolate_command.node_terminate_command')
def test_isolate_raise_exception(mock_terminate, mock_drain, mock_snapshot):
    """Test raise on exception."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    node = "node123"
    mock_snapshot.cli.side_effect = Exception()

    res = runner.invoke(cli, ['-n', node], obj=env)

    assert isinstance(res.exception, Exception)
    mock_snapshot.cli.assert_called_with(node=node)
    mock_drain.cli.assert_not_called()
    mock_terminate.cli.assert_not_called()
