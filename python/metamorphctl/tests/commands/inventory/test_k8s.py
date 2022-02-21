# -*- coding: utf-8 -*-
"""K8s inventory tests."""

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

import json
from unittest import mock

from kubernetes.client import (ApiClient, ApiextensionsV1beta1Api, CustomObjectsApi)
from kubernetes.client.rest import ApiException
from mock import patch, Mock

from metamorphctl.utils.config import Config
from metamorphctl.commands.inventory.k8s import Kubernetes

# pylint: disable=unused-argument


def test_collect_with_empty_resources():
    """Test when there is no k8s resource to collect from."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {'kubernetes': []}
        result = Kubernetes().collect()
        assert not result  # empty result


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
@patch('metamorphctl.commands.inventory.k8s.find_api_in_kubernetes')
def test_collect_with_single_resource(mock_find_api, mock_load_kubernetes):
    """Test when there is a single resource to collect from."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {"kubernetes": [{"title": "myresource", "api": "random-api"}]}
        myresource_value = {"items": ["something"]}
        mock_find_api.return_value = lambda: myresource_value
        expected = {"myresource": myresource_value["items"]}

        result = Kubernetes().collect()

        mock_find_api.assert_called()
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
@patch('metamorphctl.commands.inventory.k8s.find_api_in_kubernetes')
def test_continue_collecting_on_api_exception(mock_find_api, mock_load_kubernetes):
    """Test it continues collecting on ApiException."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "pod",
                "api": "pod"
            }, {
                "title": "node",
                "api": "node"
            }]
        }
        pod_value = {'error': 'Not Found'}
        node_value = {'items': ['bar']}
        expected = {'pod': pod_value, 'node': node_value['items']}
        # raise exception for the first call, but not for the second
        mock_find_api.side_effect = [
            lambda: _raise(ApiException(reason='Not Found')), lambda: node_value
        ]

        result = Kubernetes().collect()

        assert mock_find_api.call_count == 2
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
@patch('metamorphctl.commands.inventory.k8s.find_api_in_kubernetes')
def test_continue_collecting_on_value_error_exception(mock_find_api, mock_load_kubernetes):
    """Test it continues collecting on ApiException."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "pod",
                "api": "pod"
            }, {
                "title": "node",
                "api": "node"
            }]
        }
        pod_value = {'error': ''}
        node_value = {'items': ['bar']}
        expected = {'pod': pod_value, 'node': node_value['items']}
        # raise exception for the first call, but not for the second
        mock_find_api.side_effect = [lambda: _raise(ValueError()), lambda: node_value]

        result = Kubernetes().collect()

        assert mock_find_api.call_count == 2
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
@patch('metamorphctl.commands.inventory.k8s.find_api_in_kubernetes')
def test_collect_list_controller_revision_for_all_namespaces(mock_find_api, mock_load_kubernetes):
    """Test collect works with list_controller_revision_for_all_namespaces."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "list_controller_revision_for_all_namespaces",
                "api": "list_controller_revision_for_all_namespaces"
            }]
        }
        resource_value = {'items': ['bar']}
        expected = {'list_controller_revision_for_all_namespaces': resource_value['items']}
        mock_find_api.return_value = lambda _preload_content: Mock(data=json.dumps(resource_value))

        result = Kubernetes().collect()

        mock_find_api.assert_called()
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
@patch('metamorphctl.commands.inventory.k8s.find_api_in_kubernetes')
def test_collect_list_api_service(mock_find_api, mock_load_kubernetes):
    """Test collect works with list_api_service."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "list_api_service",
                "api": "list_api_service"
            }]
        }
        resource_value = {'items': ['bar']}
        expected = {'list_api_service': resource_value['items']}
        mock_find_api.return_value = lambda _preload_content: Mock(data=json.dumps(resource_value))

        result = Kubernetes().collect()

        mock_find_api.assert_called()
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
def test_collect_list_pod_metrics(mock_load_kubernetes):
    """Test collect works with list_pod_metrics."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config, \
            mock.patch.object(ApiClient, 'call_api') as mock_api_client:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "list_pod_metrics",
                "api": "list_pod_metrics"
            }]
        }
        resource_value = {'items': ['bar']}
        expected = {'list_pod_metrics': resource_value['items']}
        mock_api_client.return_value = [Mock(data=json.dumps(resource_value))]

        result = Kubernetes().collect()

        mock_api_client.assert_called()
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
def test_collect_list_node_metrics(mock_load_kubernetes):
    """Test collect works with list_node_metrics."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config, \
            mock.patch.object(ApiClient, 'call_api') as mock_api_client:
        mocked_config.return_value = {
            "kubernetes": [{
                "title": "list_node_metrics",
                "api": "list_node_metrics"
            }]
        }
        resource_value = {'items': ['bar']}
        expected = {'list_node_metrics': resource_value['items']}
        mock_api_client.return_value = [Mock(data=json.dumps(resource_value))]

        result = Kubernetes().collect()

        mock_api_client.assert_called()
        assert result == expected


@patch('metamorphctl.commands.inventory.k8s.load_kubernetes')
def test_collect_list_cluster_custom_object(mock_load_kubernetes):
    """Test collect works with list_cluster_custom_object."""

    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config, \
            mock.patch.object(
                ApiextensionsV1beta1Api, 'list_custom_resource_definition') as mock_custom, \
            mock.patch.object(CustomObjectsApi, 'list_cluster_custom_object') as mock_cluster_api:

        mocked_config.return_value = {
            "kubernetes": [{
                "title": "list_cluster_custom_object",
                "api": "list_cluster_custom_object"
            }]
        }

        monitoring_params = {
            'metadata.name': 'monitoring_core_os',
            'spec.group': 'core_os',
            'spec.version': 'v1',
            'spec.names.plural': 'plural'
        }
        calico_params = {
            'metadata.name': 'crd_projectcalico_org',
            'spec.group': 'projectcalico_org',
            'spec.version': 'v1',
            'spec.names.plural': 'plural'
        }
        monitoring_core_os = Mock(**monitoring_params)
        crd_projectcalico_org = Mock(**calico_params)
        custom_resources = Mock(items=[monitoring_core_os, crd_projectcalico_org])

        monitoring_core_os_value = {'foo': 'bar'}
        crd_projectcalico_org_value = {'some': 'value'}
        mock_custom.return_value = custom_resources
        mock_cluster_api.side_effect = [monitoring_core_os_value, crd_projectcalico_org_value]
        expected = {
            'list_cluster_custom_object': [{
                'crd_projectcalico_org': crd_projectcalico_org_value,
                'monitoring_core_os': monitoring_core_os_value
            }]
        }

        result = Kubernetes().collect()

        mock_custom.assert_called()
        assert mock_cluster_api.call_count == 2
        mock_cluster_api.assert_any_call('core_os', 'v1', 'plural')
        mock_cluster_api.assert_any_call('projectcalico_org', 'v1', 'plural')
        assert result == expected


def _raise(ex):
    raise ex
