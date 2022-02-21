# -*- coding: utf-8 -*-
"""Kubernetes collector."""

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
import jmespath

from kubernetes import client
from kubernetes.client.rest import ApiException

from metamorphctl.utils.config import Config
from metamorphctl.utils.kubeutils import (find_api_in_kubernetes, load_kubernetes)


class Kubernetes():
    """Class to handle kubernetes collector."""

    def collect(self):  # pylint: disable=no-self-use
        """Collect kubernetes resources."""
        response = {}
        k8s_resources = Config().get("inventory").get("kubernetes")
        if not k8s_resources:
            return response
        load_kubernetes()
        for req in k8s_resources:
            try:
                title = req['title']
                print('Collecting k8s: {}'.format(title))
                res = _handle_request(req)
                response[title] = res
            except ApiException as ex:
                print("No data for {} to be collected".format(title))
                response[title] = {'error': ex.reason}
            except Exception as ex:  # pylint: disable=broad-except
                print("Exception been caught, error:", ex)
                response[title] = {'error': str(ex)}
        return response


def _handle_request(req):
    """Handle collection of items."""
    res = []
    resource = req['api']

    # Invoke our workaround function if exists
    if resource in globals():
        out = globals()[resource]()
    # Else, let k8s do the work
    else:
        k8s_api = find_api_in_kubernetes(resource)
        out = client.ApiClient().sanitize_for_serialization(k8s_api())
    res += jmespath.search("items[]", out)

    return res


def list_controller_revision_for_all_namespaces():
    """Workaround for list_controller_revision_for_all_namespaces."""
    return _execute_k8s_api_raw('list_controller_revision_for_all_namespaces')


def list_api_service():
    """Workaround for list_api_service."""
    return _execute_k8s_api_raw('list_api_service')


def list_cluster_custom_object():
    """Workaround for list_cluster_custom_object."""
    custom_resources = client.ApiextensionsV1beta1Api().list_custom_resource_definition()
    result = {}
    for resource in custom_resources.items:
        name = resource.metadata.name
        group = resource.spec.group
        version = resource.spec.version
        plural = resource.spec.names.plural
        output = client.CustomObjectsApi().list_cluster_custom_object(group, version, plural)
        sanitized_output = client.ApiClient().sanitize_for_serialization(output)
        result[name] = sanitized_output
    return {"items": [result]}


def list_pod_metrics():
    """Workaround for list_pod_metrics."""
    return _execute_k8s_metrics_raw('/apis/metrics.k8s.io/v1beta1/pods/')


def list_node_metrics():
    """Workaround for list_node_metrics."""
    return _execute_k8s_metrics_raw('/apis/metrics.k8s.io/v1beta1/nodes/')


def _execute_k8s_api_raw(api_name):
    k8s_api = find_api_in_kubernetes(api_name)
    result = k8s_api(_preload_content=False)
    return json.loads(result.data)


def _execute_k8s_metrics_raw(metric_name):
    result = client.ApiClient().call_api(
        metric_name,
        'GET',
        auth_settings=['BearerToken'],
        response_type='json',
        _preload_content=False)
    return json.loads(result[0].data)
