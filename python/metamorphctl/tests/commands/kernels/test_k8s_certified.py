# -*- coding: utf-8 -*-
"""Kernel K8s:certified tests."""

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

import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

from metamorphctl.commands.kernels.k8s_certified import K8sCertifiedOperator


@patch.dict('os.environ', clear=True)
@patch('metamorphctl.commands.kernels.k8s_certified.open', mock_open())
@patch('boto3.client')
def test_initialize_set_env_variables(boto_mock):
    """Test initialize set env variables."""
    env = MagicMock()
    namespace, key, secret, region = 'namespace', 'key', 'secret', 'region'
    operator = K8sCertifiedOperator(env, namespace, key, secret, region)

    operator.initialize()

    boto_mock.return_value.describe_cluster.assert_called()
    assert os.environ['KERNEL_NAMESPACE'] == namespace
    assert os.environ['AWS_ACCESS_KEY_ID'] == key
    assert os.environ['AWS_SECRET_ACCESS_KEY'] == secret
    assert os.environ['AWS_DEFAULT_REGION'] == region


@patch.dict('os.environ', clear=True)
@patch('metamorphctl.commands.kernels.k8s_certified.open', mock_open())
@patch('boto3.client')
def test_initialize_set_environment_with_kubeconfig(boto_mock):
    """Test initialize set environment with kubeconfig."""
    env = MagicMock()
    namespace, key, secret, region = 'namespace', 'key', 'secret', 'region'
    kubeconfig_path = os.path.join(tempfile.gettempdir(), namespace)
    operator = K8sCertifiedOperator(env, namespace, key, secret, region)

    operator.initialize()

    boto_mock.return_value.describe_cluster.assert_called()

    assert env.kubeconfig == kubeconfig_path


@patch.dict('os.environ', clear=True)
@patch('metamorphctl.commands.kernels.k8s_certified.open', new_callable=mock_open)
@patch('boto3.client')
def test_initialize_writes_kubeconfig_to_temp_dir(boto_mock, file_mock):
    """Test initialize writes kubeconfig to temp dir."""
    env = MagicMock()
    namespace, key, secret, region = 'namespace', 'key', 'secret', 'region'
    kubeconfig_path = os.path.join(tempfile.gettempdir(), namespace)
    operator = K8sCertifiedOperator(env, namespace, key, secret, region)

    operator.initialize()

    boto_mock.return_value.describe_cluster.assert_called()
    file_mock.assert_called_with(kubeconfig_path, 'w+')


@patch('metamorphctl.commands.kernels.k8s_certified.load_kubernetes', lambda: None)
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_validate_return_true_on_validation_success(boto_mock, k8s_mock):
    """Test validate."""
    operator = K8sCertifiedOperator(MagicMock, 'namespace', 'key', 'secret', 'region')

    result = operator.validate()

    assert result
    boto_mock.return_value.get_user.assert_called()
    k8s_mock.return_value.list_namespace.assert_called()


@patch('metamorphctl.commands.kernels.k8s_certified.load_kubernetes', lambda: None)
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_validate_return_false_on_validation_failure(boto_mock, k8s_mock):
    """Test validate."""
    operator = K8sCertifiedOperator(MagicMock, 'namespace', 'key', 'secret', 'region')
    boto_mock.side_effect = Exception
    k8s_mock.side_effect = Exception

    result = operator.validate()

    assert not result
