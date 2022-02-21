# -*- coding: utf-8 -*-
"""Test shellinit command."""

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

from metamorphctl.commands.shellinit_command import cli


@patch('metamorphctl.commands.shellinit_command.exists', lambda x: False)
@patch('metamorphctl.commands.shellinit_command.system')
def test_return_when_bind_file_does_not_exist(system_mock):
    """Test shellinit run with multiple assertions."""
    runner = CliRunner()
    runner.invoke(cli, '-b bind -o k8s:certified -u key -s secret')
    system_mock.assert_not_called()


@patch('metamorphctl.commands.shellinit_command.exists', lambda x: True)
@patch('boto3.client', lambda *args, **argv: MagicMock())
@patch('metamorphctl.commands.shellinit_command.system')
@patch('metamorphctl.commands.shellinit_command.copy')
@patch('metamorphctl.commands.shellinit_command.Cd')
def test_shellinit_run(cd_mock, copy_mock, system_mock):
    """Test shellinit run with multiple assertions."""
    runner = CliRunner()

    res = runner.invoke(cli, '-b bind -o k8s:certified -u key -s secret')

    assert res.exit_code == 0, res.output
    copy_mock.assert_called_with('bind', '.shellinit')
    cd_mock.assert_called_with('.shellinit')
    system_mock.assert_called_with(
        """metamorph shellinit """
        """--options=bind,ACCESS_KEY=key,SECRET_KEY=secret --onkernel=k8s:certified""")
