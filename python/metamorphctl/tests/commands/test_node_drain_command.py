# -*- coding: utf-8 -*-
"""Node drain command tests."""

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

from subprocess import CalledProcessError
from unittest.mock import patch

from click.testing import CliRunner

from metamorphctl.cli import Environment
from metamorphctl.commands.node_drain_command import cli


@patch('subprocess.run')
def test_no_drain_node_without_confirmation(subprocess_mock):
    """Test should not drain without confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False

    res = runner.invoke(cli, ['-n', 'node'], obj=env)

    assert res.exit_code != 0, res.output
    subprocess_mock.assert_not_called()


@patch('subprocess.run')
def test_drain_node_with_confirmation(subprocess_mock):
    """Test drain node with confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True

    res = runner.invoke(cli, ['-n', 'node'], obj=env)

    assert res.exit_code == 0, res.output
    subprocess_mock.assert_called()


@patch('subprocess.run')
def test_drain_node_raises_called_process_error(subprocess_mock):
    """Test raise on exception."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    subprocess_mock.side_effect = CalledProcessError(returncode=1, cmd='cmd')

    res = runner.invoke(cli, ['-n', 'node'], obj=env)

    assert isinstance(res.exception, CalledProcessError)
    subprocess_mock.assert_called()


@patch('subprocess.run')
def test_drain_node_raises_exception(subprocess_mock):
    """Test raise on exception."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    subprocess_mock.side_effect = Exception()

    res = runner.invoke(cli, ['-n', 'node'], obj=env)

    assert isinstance(res.exception, Exception)
    subprocess_mock.assert_called()
