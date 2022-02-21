# -*- coding: utf-8 -*-
"""Isolate label command tests."""

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

from click.testing import CliRunner
from kubernetes.client import CoreV1Api

from metamorphctl.cli import Environment
from metamorphctl.commands.label_isolate_command import cli


@patch('metamorphctl.commands.label_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.label_isolate_command.pod_isolate_command')
@patch.object(CoreV1Api, 'list_namespaced_pod')
def test_isolate_no_pods_found(mock_k8s, mock_pod_isolate_command):
    """Test isolate when no pod has been found."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    mock_k8s.return_value.items = []

    res = runner.invoke(cli, ['-l', 'mylabel', '-n', 'myns'], obj=env)

    assert res.exit_code == 0, res.output
    mock_pod_isolate_command.cli.assert_not_called()


@patch('metamorphctl.commands.label_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.label_isolate_command.pod_isolate_command')
@patch.object(CoreV1Api, 'list_namespaced_pod')
def test_no_isolate_pod_without_confirmation(mock_k8s, mock_pod_isolate_command):
    """Test should not isolate without confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False
    mock_k8s.return_value.items = [Mock()]

    res = runner.invoke(cli, ['-l', 'mylabel', '-n', 'myns'], obj=env)

    assert res.exit_code != 0, res.output
    mock_pod_isolate_command.cli.assert_not_called()


@patch('metamorphctl.commands.label_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.label_isolate_command.pod_isolate_command')
@patch.object(CoreV1Api, 'list_namespaced_pod')
def test_isolate_pods_with_confirmation(mock_k8s, mock_pod_isolate_command):
    """Test isolate pods with confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True
    mock_k8s.return_value.items = [Mock(), Mock()]

    res = runner.invoke(cli, ['-l', 'mylabel', '-n', 'myns'], obj=env)

    assert res.exit_code == 0, res.output
    assert mock_pod_isolate_command.cli.call_count == 2


@patch('metamorphctl.commands.label_isolate_command.load_kubernetes', lambda: None)
@patch('metamorphctl.commands.label_isolate_command.pod_isolate_command')
@patch.object(CoreV1Api, 'list_namespaced_pod')
def test_isolate_raise_exception(mock_k8s, mock_pod_isolate_command):
    """Test raise on exception."""
    mock_k8s.side_effect = Exception()
    runner = CliRunner()
    res = runner.invoke(cli, ['-l', 'mylabel', '-n', 'myns'])
    assert isinstance(res.exception, Exception)
    mock_pod_isolate_command.cli.assert_not_called()
