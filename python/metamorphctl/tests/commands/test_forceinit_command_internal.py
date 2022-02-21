# -*- coding: utf-8 -*-
"""Force-init command tests."""

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

from metamorphctl.commands.forceinit_command_internal import cli
from metamorphctl.commands.kernels.k8s_certified import K8sCertifiedOperator


@patch.object(K8sCertifiedOperator, "__init__", lambda *args: None)
@patch.object(K8sCertifiedOperator, "validate")
@patch.object(K8sCertifiedOperator, "initialize")
def test_forceinit(initialize_mock, validate_mock):
    """Test forceinit normal flow."""
    runner = CliRunner()
    res = runner.invoke(cli, '-o k8s:certified -k namespace -u key -s secret -r region')

    assert res.exit_code == 0, res.output

    initialize_mock.assert_called()
    validate_mock.assert_called()


@patch.object(K8sCertifiedOperator, "__init__", lambda *args: None)
@patch.object(K8sCertifiedOperator, "validate", lambda *args: False)
@patch.object(K8sCertifiedOperator, "initialize")
def test_forceinit_abort_on_validation_fail(initialize_mock):
    """Test forceinit should raise exception."""
    runner = CliRunner()

    res = runner.invoke(cli, '-o k8s:certified -k namespace -u key -s secret -r region')

    assert res.exit_code != 0, res.output
    assert "Aborted!" in res.output
    initialize_mock.assert_called()


@patch.object(K8sCertifiedOperator, "__init__", lambda *args: None)
@patch.object(K8sCertifiedOperator, "validate")
@patch.object(K8sCertifiedOperator, "initialize")
def test_forceinit_raise_exception(initialize_mock, validate_mock):
    """Test forceinit should raise exception."""
    initialize_mock.side_effect = Exception()
    runner = CliRunner()

    res = runner.invoke(cli, '-o k8s:certified -k namespace -u key -s secret -r region')

    assert res.exit_code != 0, res.output
    assert isinstance(res.exception, Exception)
    validate_mock.assert_not_called()
