# -*- coding: utf-8 -*-
"""Stop eks operation tests."""

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

from metamorphctl.commands.eks_cluster.stop_eks_operation import describe, apply, _stop_rds_clusters


def test_describe():
    """Test describe."""
    assert describe()


@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.sleep', lambda x: None)
@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.load_kubernetes', lambda **arg: None)
@patch('kubernetes.client.AppsV1Api')
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_apply_when_there_are_no_machines(boto_mock, k8s_core_mock, k8s_apps_mock):
    """Test apply when there are no machines."""
    autoscaling_mock = MagicMock(name='asg')
    ec2_mock = MagicMock(name='ec2')
    rds_mock = MagicMock(name='rds')
    boto_mock.side_effect = [autoscaling_mock, ec2_mock, rds_mock]

    apply("my_namespace", True)

    autoscaling_mock.suspend_processes.assert_not_called()
    ec2_mock.stop_instances.assert_not_called()
    ec2_mock.get_waiter.return_value.wait.assert_not_called()
    ec2_mock.detach_volume.assert_not_called()


@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.sleep', lambda x: None)
@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.load_kubernetes', lambda **arg: None)
@patch('kubernetes.client.AppsV1Api')
@patch('kubernetes.client.CoreV1Api')
@patch('boto3.client')
def test_apply_when_there_are_machines(boto_mock, k8s_core_mock, k8s_apps_mock):
    """Test apply when there are machines."""
    autoscaling_mock = MagicMock(name='asg')
    ec2_mock = MagicMock(name='ec2')
    rds_mock = MagicMock(name='rds')
    boto_mock.side_effect = [autoscaling_mock, ec2_mock, rds_mock]
    # inject autoscaling group mock
    autoscaling_mock.get_paginator.return_value.paginate.return_value.search.return_value = ['asg1']
    # inject ec2 instance mock
    ec2_mock.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'ec2'
            }]
        }]
    }
    ec2_mock.describe_volumes.return_value = {'Volumes': [{'VolumeId': 'vol1'}]}

    apply("my_namespace", True)

    autoscaling_mock.suspend_processes.assert_called()
    ec2_mock.stop_instances.assert_called()
    ec2_mock.get_waiter.return_value.wait.assert_called()
    ec2_mock.detach_volume.assert_called()


@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.sleep', lambda x: None)
def test_stop_rds_clusters_when_no_clusters():
    """Test stop when there are no clusters."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.return_value = {'DBClusters': []}

    _stop_rds_clusters('test', rds_mock)

    rds_mock.stop_db_cluster.assert_not_called()


@patch('metamorphctl.commands.eks_cluster.stop_eks_operation.sleep')
def test_stop_rds_clusters_when_clusters(mock_sleep):
    """Test stop when there are clusters."""
    rds_mock = MagicMock(name='rds_client')
    rds_mock.describe_db_clusters.side_effect = [{
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'available'
        }]
    }, {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'stopping'
        }]
    }, {
        'DBClusters': [{
            'DBClusterIdentifier': 'test-cluster',
            'Status': 'stopped'
        }]
    }]

    _stop_rds_clusters('test', rds_mock)

    rds_mock.stop_db_cluster.assert_called_once_with(DBClusterIdentifier='test-cluster')
    mock_sleep.assert_called()
