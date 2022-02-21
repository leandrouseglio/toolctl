# -*- coding: utf-8 -*-
"""Start eks operation tests."""

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
from kubernetes.client.rest import ApiException
import pytest

from metamorphctl.commands.eks_cluster.start_eks_operation \
    import describe, apply, KUBE_SYSTEM, _start_rds_clusters, _wait_rds_clusters, \
    _scale_cluster_autoscaler_deploy, _delete_etcd_pods


def test_describe():
    """Test describe."""
    assert describe()


@patch('metamorphctl.commands.eks_cluster.start_eks_operation.sleep', lambda x: None)
@patch('metamorphctl.commands.eks_cluster.start_eks_operation.load_kubernetes', lambda **arg: None)
@patch('kubernetes.client.AppsV1Api')
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_apply_when_there_are_no_machines(boto_mock, k8s_core_mock, k8s_apps_mock):
    """Test apply when there are no machines."""
    autoscaling_mock = MagicMock(name='asg')
    ec2_mock = MagicMock(name='ec2')
    rds_mock = MagicMock(name='rds')
    boto_mock.side_effect = [autoscaling_mock, ec2_mock, rds_mock]
    k8s_core_mock.return_value.list_namespaced_pod.side_effect = _pods

    apply("my_namespace", True)

    # add_toleration assertions
    k8s_apps_mock.return_value.patch_namespaced_deployment.assert_called()
    k8s_apps_mock.return_value.patch_namespaced_stateful_set.assert_not_called()
    # start_instances assertions
    ec2_mock.start_instances.assert_not_called()
    ec2_mock.get_waiter.return_value.wait.assert_not_called()
    # taint_nodes / untaint_nodes assertions
    k8s_core_mock.return_value.patch_node.assert_not_called()
    # resume_autoscaling_group assertions
    autoscaling_mock.resume_processes.assert_not_called()


@patch('metamorphctl.commands.eks_cluster.start_eks_operation.sleep', lambda x: None)
@patch('metamorphctl.commands.eks_cluster.start_eks_operation.load_kubernetes', lambda **arg: None)
@patch('kubernetes.client.AppsV1Api')
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_apply_when_there_are_machines(boto_mock, k8s_core_mock, k8s_apps_mock):
    """Test apply when there are machines."""
    autoscaling_mock = MagicMock(name='asg')
    ec2_mock = MagicMock(name='ec2')
    rds_mock = MagicMock(name='rds')
    boto_mock.side_effect = [autoscaling_mock, ec2_mock, rds_mock]
    k8s_apps_mock.return_value.list_namespaced_deployment.side_effect = _deploys
    k8s_apps_mock.return_value.list_namespaced_stateful_set.side_effect = _stateful_sets
    k8s_core_mock.return_value.list_node.side_effect = _nodes
    k8s_core_mock.return_value.list_namespaced_pod.side_effect = _pods
    k8s_core_mock.return_value.list_pod_for_all_namespaces.side_effect = _list_pods
    ec2_mock.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'ec2',
                'PrivateDnsName': 'private-dns'
            }]
        }]
    }
    autoscaling_mock.get_paginator.return_value.paginate.return_value.search.return_value = ['asg1']

    apply("my_namespace", True)

    # add_toleration assertions
    k8s_apps_mock.return_value.patch_namespaced_deployment.assert_called()
    k8s_apps_mock.return_value.patch_namespaced_stateful_set.assert_called()
    # start_instances assertions
    ec2_mock.start_instances.assert_called()
    ec2_mock.get_waiter.return_value.wait.assert_called()
    # wait_nodes_readiness assertions
    k8s_core_mock.return_value.list_node.assert_called()
    # wait_etcd_cluster assertions
    k8s_core_mock.return_value.list_namespaced_pod.assert_called()
    # taint_nodes / untaint_nodes assertions
    k8s_core_mock.return_value.patch_node.assert_called()
    # resume_autoscaling_group assertions
    autoscaling_mock.resume_processes.assert_called()


def _nodes():
    nodes = MagicMock()
    node1_params = {
        'metadata.name': 'node1',
        'status.conditions': [MagicMock(type='Ready', status='True')]
    }
    node1 = MagicMock(**node1_params)
    nodes.items = [node1]
    return nodes


def _pods(namespace=None, label_selector=None):
    pods = MagicMock()
    if namespace == KUBE_SYSTEM and label_selector == 'app=etcd':
        pods.items = [MagicMock(), MagicMock(), MagicMock()]
    return pods


def _list_pods(watch=False):
    # pylint: disable=unused-argument
    pods = MagicMock()
    pods.items = [MagicMock(), MagicMock()]
    return pods


def _deploys(namespace=None):
    deploys = MagicMock()
    if namespace == KUBE_SYSTEM:
        deploys.items = [MagicMock()]
    return deploys


def _stateful_sets(namespace=None):
    stateful_sets = MagicMock()
    if namespace == KUBE_SYSTEM:
        stateful_sets.items = [MagicMock()]
    return stateful_sets


def test_start_rds_clusters_when_no_clusters():
    """Test start when there are no clusters."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.return_value = {'DBClusters': []}

    _start_rds_clusters('test', rds_mock)

    rds_mock.start_db_cluster.assert_not_called()


@patch('metamorphctl.commands.eks_cluster.start_eks_operation.sleep')
def test_start_rds_clusters_when_clusters(mock_sleep):
    """Test stop when there are clusters."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.side_effect = [{
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'stopped'
        }]
    }, {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'starting'
        }]
    }, {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'available'
        }]
    }]

    _start_rds_clusters('test', rds_mock)

    rds_mock.start_db_cluster.assert_called_once_with(DBClusterIdentifier='test-cluster')
    mock_sleep.assert_called_once()


@patch('metamorphctl.commands.eks_cluster.start_eks_operation.sleep')
def test_wait_rds_cluster_when_matchs_desired(sleep_mock):
    """Test wait breaks when available matchs desired."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.return_value = {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'available'
        }, {
            'DBClusterIdentifier': 'id2',
            'Status': 'stopped'
        }, {
            'DBClusterIdentifier': 'test-cluster2',
            'Status': 'stopped'
        }]
    }

    _wait_rds_clusters(['test-cluster'], rds_mock)

    sleep_mock.assert_not_called()


@patch('metamorphctl.commands.eks_cluster.start_eks_operation.sleep')
def test_wait_rds_cluster_when_no_matchs_desired(sleep_mock):
    """Test wait breaks when available not matchs desired."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.side_effect = [{
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'stopped'
        }]
    }, {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'available'
        }]
    }]

    _wait_rds_clusters(['test-cluster'], rds_mock)

    sleep_mock.assert_called_once()


@patch('kubernetes.client.AppsV1Api')
def test_scale_autoscaler_when_succeed(k8s_apps_mock):
    """Test scale_autoscaler method when patch succeeds."""
    _scale_cluster_autoscaler_deploy(1)
    k8s_apps_mock.return_value.patch_namespaced_deployment.assert_called_once()


@patch('kubernetes.client.AppsV1Api')
def test_scale_autoscaler_when_failed(k8s_apps_mock):
    """Test scale_autoscaler method when patch fails."""
    k8s_apps_mock.return_value.patch_namespaced_deployment.side_effect = ApiException()
    with pytest.raises(RuntimeError):
        _scale_cluster_autoscaler_deploy(1)


@patch('kubernetes.client.CoreV1Api')
def test_delete_etcd_pods_when_no_pods(k8s_core_mock):
    """Test no pods deleted when no etcd pods."""
    k8s_core_mock.return_value.list_namespaced_pod.return_value = MagicMock(items=[])
    _delete_etcd_pods()
    k8s_core_mock.return_value.delete_namespaced_pod.assert_not_called()


@patch('kubernetes.client.CoreV1Api')
def test_delete_etcd_pods_when_pods(k8s_core_mock):
    """Test pods deleted when etcd pods."""
    k8s_core_mock.return_value.list_namespaced_pod.return_value = MagicMock(items=[MagicMock()])
    _delete_etcd_pods()
    k8s_core_mock.return_value.delete_namespaced_pod.assert_called_once()


@patch('kubernetes.client.CoreV1Api')
def test_delete_etcd_pods_ignore_exception(k8s_core_mock):
    """Test pods deleted when etcd pods."""
    k8s_core_mock.return_value.list_namespaced_pod.return_value = MagicMock(items=[MagicMock()])
    k8s_core_mock.return_value.delete_namespaced_pod.side_effect = ApiException()
    _delete_etcd_pods()
    k8s_core_mock.return_value.delete_namespaced_pod.assert_called_once()
