# -*- coding: utf-8 -*-
"""EKS command tests."""

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
from metamorphctl.commands.eks_cluster import start_eks_operation
from metamorphctl.commands.eks_command import cli


@patch.object(start_eks_operation, 'apply')
@patch.object(start_eks_operation, 'describe')
def test_no_eks_apply_without_confirmation(describe_mock, apply_mock):
    """Test should not apply without confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False

    res = runner.invoke(cli, ['-a', 'start', '-k', 'myns'], obj=env)

    assert res.exit_code != 0, res.output
    # describe is called before asking for confirmation
    describe_mock.assert_called()
    apply_mock.assert_not_called()


@patch.object(start_eks_operation, 'apply')
@patch.object(start_eks_operation, 'describe')
def test_eks_apply_with_confirmation(describe_mock, apply_mock):
    """Test should apply with confirmation."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True

    res = runner.invoke(cli, ['-a', 'start', '-k', 'myns'], obj=env)

    assert res.exit_code == 0, res.output
    describe_mock.assert_called()
    apply_mock.assert_called()
