# -*- coding: utf-8 -*-
"""VPC sealing command tests."""

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
from metamorphctl.commands.vpc_sealing.operation_util import OperationUtil
from metamorphctl.commands.vpc_sealing.permit_by_exception_operation import \
    PermitByExceptionOperation
from metamorphctl.commands.vpc_sealing_command import cli


@patch.object(OperationUtil, "__init__", lambda x, y: None)
@patch.object(PermitByExceptionOperation, "__init__", lambda x, y: None)
@patch.object(PermitByExceptionOperation, "describe")
@patch.object(PermitByExceptionOperation, "apply")
def test_run_with_apply(mocked_apply, mocked_describe):
    """Test if method works properly."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = True

    res = runner.invoke(cli, '--operation permit-by-exception --vpc_id vpc', obj=env)

    assert res.exit_code == 0, res.output
    mocked_describe.assert_called()
    mocked_apply.assert_called()


@patch.object(OperationUtil, "__init__", lambda x, y: None)
@patch.object(PermitByExceptionOperation, "__init__", lambda x, y: None)
@patch.object(PermitByExceptionOperation, "describe")
@patch.object(PermitByExceptionOperation, "apply")
def test_run_with_no_apply(mocked_apply, mocked_describe):
    """Test if method works properly."""
    runner = CliRunner()
    env = Environment()
    env.autoconfirm = False

    res = runner.invoke(cli, '--operation permit-by-exception --vpc_id vpc', obj=env)

    assert res.exit_code != 0, res.output
    mocked_describe.assert_called()
    mocked_apply.assert_not_called()
