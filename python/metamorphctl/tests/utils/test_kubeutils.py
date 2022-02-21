# -*- coding: utf-8 -*-
"""Test kubernetes utils."""

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

import uuid

import pytest
from kubernetes import client

from metamorphctl.utils.kubeutils import (SelectorOperator, SelectorParser,
                                          find_api_in_kubernetes)


@pytest.mark.parametrize("selector, labels", [
    (client.V1LabelSelector(
        match_expressions=None, match_labels={'app': 'mysql-client'}), {
            'app': 'mysql-client'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.IN, values=['one']),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.NOT_IN, values=['two'])
        ],
        match_labels=None), {
            'foo': 'one',
            'bar': 'nottwo'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.EXISTS, values=[]),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.DOES_NOT_EXIST, values=[])
        ],
        match_labels=None), {
            'foo': 'one',
            'notbar': 'two'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.IN,
                values=['two', 'one', 'three']),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.EXISTS, values=[])
        ],
        match_labels={'app': 'mysql-client'}), {
            'app': 'mysql-client',
            'foo': 'one',
            'bar': 'bar'
    })
])
def test_match(selector, labels):
    """Test if labels are matched by selector."""
    parser = SelectorParser(selector)
    matched = parser.matches(labels)
    assert matched


@pytest.mark.parametrize("selector, labels", [
    (client.V1LabelSelector(
        match_expressions=None, match_labels={'app': 'nginx'}), {
            'app': 'mysql-client'
    }),
    (client.V1LabelSelector(
        match_expressions=None, match_labels={'app': 'nginx'}), {
            'notapp': 'nginx'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.NOT_IN, values=['one']),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.NOT_IN, values=['two'])
        ],
        match_labels=None), {
            'foo': 'one',
            'bar': 'nottwo'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.DOES_NOT_EXIST, values=[]),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.EXISTS, values=[])
        ],
        match_labels=None), {
            'foo': 'one',
            'notbar': 'two'
    }),
    (client.V1LabelSelector(
        match_expressions=[
            client.V1LabelSelectorRequirement(
                key='foo', operator=SelectorOperator.NOT_IN,
                values=['two', 'one', 'three']),
            client.V1LabelSelectorRequirement(
                key='bar', operator=SelectorOperator.EXISTS, values=[])
        ],
        match_labels={'app': 'mysql-client'}), {
            'app': 'mysql-client',
            'foo': 'one',
            'bar': 'bar'
    })
])
def test_no_match(selector, labels):
    """Test if labels are not matched by selector."""
    parser = SelectorParser(selector)
    matched = parser.matches(labels)
    assert not matched


# Test which finds the "list APIs" in python k8s library.
# In the unlikely case it fails, it probably means a python k8s API changed.
@pytest.mark.parametrize("api_name", ['list_audit_sink', 'list_certificate_signing_request', 'list_cluster_custom_object', 'list_cluster_role', 'list_cluster_role_binding', 'list_component_status', 'list_csi_driver', 'list_csi_node', 'list_custom_resource_definition', 'list_mutating_webhook_configuration', 'list_namespace', 'list_node', 'list_persistent_volume', 'list_pod_security_policy', 'list_priority_class', 'list_runtime_class', 'list_storage_class', 'list_validating_webhook_configuration', 'list_volume_attachment', 'list_config_map_for_all_namespaces', 'list_controller_revision_for_all_namespaces', 'list_cron_job_for_all_namespaces', 'list_daemon_set_for_all_namespaces', 'list_deployment_for_all_namespaces', 'list_endpoints_for_all_namespaces', 'list_event_for_all_namespaces', 'list_horizontal_pod_autoscaler_for_all_namespaces', 'list_ingress_for_all_namespaces', 'list_job_for_all_namespaces', 'list_lease_for_all_namespaces', 'list_limit_range_for_all_namespaces', 'list_network_policy_for_all_namespaces', 'list_persistent_volume_claim_for_all_namespaces', 'list_pod_disruption_budget_for_all_namespaces', 'list_pod_for_all_namespaces', 'list_pod_preset_for_all_namespaces', 'list_pod_template_for_all_namespaces', 'list_replica_set_for_all_namespaces', 'list_replication_controller_for_all_namespaces', 'list_resource_quota_for_all_namespaces', 'list_role_binding_for_all_namespaces', 'list_role_for_all_namespaces', 'list_secret_for_all_namespaces', 'list_service_account_for_all_namespaces', 'list_service_for_all_namespaces', 'list_stateful_set_for_all_namespaces'])  # noqa
def test_succeed_when_api_is_found_in_kubernetes(api_name):
    """Test find_api_in_kubernetes."""
    obj = find_api_in_kubernetes(api_name)
    assert obj


def test_raise_when_api_is_not_found_in_kubernetes():
    """Test find_api_in_kubernetes."""
    api_name = str(uuid.uuid4())
    with pytest.raises(AttributeError):
        find_api_in_kubernetes(api_name)
