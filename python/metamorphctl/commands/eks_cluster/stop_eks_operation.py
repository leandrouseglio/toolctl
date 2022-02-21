# -*- coding: utf-8 -*-
"""Stop EKS cluster operation."""

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

import copy
from time import sleep
import boto3
import yaml

from kubernetes import client
from kubernetes.client.rest import ApiException

from metamorphctl.utils.kubeutils import load_kubernetes, taint_nodes
from metamorphctl.utils.printutils import print_warn, print_success

KUBE_SYSTEM = 'kube-system'
LEGACY_SKYDNS = 'legacy-skydns'
TOLERATION_KEY = 'start_stop'
TOLERATION_YAML = '''
spec:
  template:
    spec:
      tolerations:
      - key: "start_stop"
        operator: Equal
        value: "no_toleration"
'''


def describe():
    """Describe stop eks operation."""
    return "About to stop an eks cluster"


def apply(namespace, stop_rds):
    """Orchestrate the EKS environment stop."""
    load_kubernetes()
    autoscaling_client = boto3.client('autoscaling')
    ec2_client = boto3.client('ec2')
    rds_client = boto3.client('rds')

    print_warn("\n\n== PAUSING AUTOSCALING GROUP ==\n\n------------ASG---------------\n")
    _pause_autoscaling_groups(namespace, autoscaling_client)

    print_warn("\n\n== REMOVING TOLERATION FOR kube-system and legacy-skydns ==")
    _remove_toleration(KUBE_SYSTEM)
    _remove_toleration(LEGACY_SKYDNS)

    print_warn('\n\n== Taint k8s Nodes ==\nTaint nodes for the next start\n')
    taint_nodes()

    print_warn("\n\n== WAITING FOR PODS EVACUATION ==")
    sleep(60)

    print_warn("\n\n== STOPPING INSTANCES ==\n\n------------INSTANCES---------------\n")
    _stop_instances(namespace, ec2_client)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn("\n\n== DELETING PODS ==")
    _delete_pods([])

    print_warn("\n\n== DETACHING KUBERNETES VOLUMES ==\n\n------------VOLUMES---------------\n")
    _detach_kubernetes_volumes(namespace, ec2_client)

    if stop_rds:
        print_warn("\n\n== STOPPING RDS INSTANCES ==\n\n------------RDS---------------\n")
        _stop_rds_clusters(namespace, rds_client)

    print_success("DONE\n\n-->{} STOPPED!<--".format(namespace))


def _delete_pods(exclude_namespaces):
    kube_core_client = client.CoreV1Api()
    pods_list = kube_core_client.list_pod_for_all_namespaces(watch=False)
    pods_list = [pod for pod in pods_list.items if pod.metadata.namespace not in exclude_namespaces]

    for pod in pods_list:
        print("Deleting pod: {pod}, in "
              "namespace: "
              "{namespace}".format(pod=pod.metadata.name, namespace=pod.metadata.namespace))
        try:
            kube_core_client.delete_namespaced_pod(
                pod.metadata.name, pod.metadata.namespace, grace_period_seconds=0)
        except ApiException as ex:
            print('Pod cannot be delete, ignoring error: {}. IGNORING.... '.format(ex.reason))


def _pause_autoscaling_groups(namespace, autoscaling_client):
    """Suspend the autoscaling group processes."""
    paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups')
    page_iterator = paginator.paginate(PaginationConfig={'PageSize': 100})
    auto_scaling_groups = list(
        page_iterator.search(
            "AutoScalingGroups[?contains(Tags[?Key=='KubernetesCluster'].Value,'{}')].[AutoScalingGroupName]".  # noqa
            format(namespace)))
    if auto_scaling_groups:
        print("Suspending {} autoscaling groups".format(len(auto_scaling_groups)))
        for group in auto_scaling_groups:
            print("Suspending {}".format(group[0]))
            autoscaling_client.suspend_processes(AutoScalingGroupName=group[0])
    else:
        print("No autoscaling groups to be suspended, SKIPPING SUSPEND OF ASG")


def _remove_toleration(namespace):
    """Add toleration to deployments and stateful sets.

    It uses the toleration data loaded from TOLERATION_YAML
    If it already had tolerations, the start_stop one is appended to avoid losing them.
    """
    kube_apps_client = client.AppsV1Api()
    print('\nGetting deployments, statefull sets, replica sets and '
          'daemons sets in: {namespace}'.format(namespace=namespace))
    toleration_data = yaml.load(TOLERATION_YAML, Loader=yaml.SafeLoader)

    deployments = kube_apps_client.list_namespaced_deployment(namespace)
    statefull_sets = kube_apps_client.list_namespaced_stateful_set(namespace)
    daemon_set = kube_apps_client.list_namespaced_daemon_set(namespace)
    replica_sets = kube_apps_client.list_namespaced_replica_set(namespace)

    deployments_items = [(item, kube_apps_client.patch_namespaced_deployment)
                         for item in deployments.items]
    statefull_sets_items = [(item, kube_apps_client.patch_namespaced_stateful_set)
                            for item in statefull_sets.items]
    replica_sets_items = [(item, kube_apps_client.patch_namespaced_replica_set)
                          for item in replica_sets.items if not item.metadata.owner_references
                          ]  # This prevents patching RS owned by deployments
    daemon_set_items = [(item, kube_apps_client.patch_namespaced_daemon_set)
                        for item in daemon_set.items
                        if (item.metadata.name in ["aws-node", "kube-proxy"])]

    print('\nAdding toleration "no_toleration" to deployments, statefull_sets and '
          'daemons sets in {namespace}: '.format(namespace=namespace))
    for item, path_function in (
            deployments_items + statefull_sets_items + daemon_set_items + replica_sets_items):
        print('Patching {}'.format(item.metadata.name))
        toleration = copy.deepcopy(toleration_data)
        if item.spec.template.spec.tolerations:
            former_tolerations = filter(lambda t: t.key != TOLERATION_KEY,
                                        item.spec.template.spec.tolerations)
            toleration['spec']['template']['spec']['tolerations'] += former_tolerations

        path_function(item.metadata.name, namespace, body=toleration)


def _stop_instances(namespace, ec2_client):
    """Stop the EC2 instances."""
    instance_objects = ec2_client.describe_instances(Filters=[
        {
            'Name': 'tag:KubernetesCluster',
            'Values': [namespace]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        },
    ])
    instances = []
    for reservation in instance_objects['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])

    if instances:
        print("Stopping cluster {}, instances: {}".format(namespace, instances))
        ec2_client.stop_instances(InstanceIds=instances)

        print("Waiting for all the instances being stopped")
        ec2_client.get_waiter('instance_stopped').wait(InstanceIds=instances)
    else:
        print("No instances to be stopped, SKIPPING STOPPING OF THE INSTANCES")


def _detach_kubernetes_volumes(namespace, ec2_client):
    """Detach only the kubernetes volumes.

    We need to detach kubernetes volumes as sometimes when we start
    the kernel again, they might not get reattached to other nodes.
    """
    volume_objects = ec2_client.describe_volumes(
        Filters=[{
            'Name': 'tag:kubernetes.io/cluster/{}'.format(namespace),
            'Values': ['owned']
        }, {
            'Name': 'tag-key',
            'Values': ['kubernetes.io/created-for/pv/name']
        }, {
            'Name': 'status',
            'Values': ['in-use']
        }])
    volumes = [volume['VolumeId'] for volume in volume_objects['Volumes']]

    for volume in volumes:
        print("Detaching: {}".format(volume))
        ec2_client.detach_volume(VolumeId=volume, Force=True)


def _stop_rds_clusters(namespace, rds_client):
    """Stop the RDS instances."""
    clusters = rds_client.describe_db_clusters()
    available_clusters = [
        cluster['DBClusterIdentifier'] for cluster in clusters['DBClusters']
        if namespace in cluster['DBClusterIdentifier'] and cluster['Status'] == 'available'
    ]

    if available_clusters:
        for cluster in available_clusters:
            print("Stopping cluster: {}".format(cluster))
            rds_client.stop_db_cluster(DBClusterIdentifier=cluster)

    else:
        print("No clusters to be stopped, SKIPPING STOPPING OF THE RDS CLUSTERS")

    stopped = False
    while not stopped:
        sleep(10)
        clusters = rds_client.describe_db_clusters()
        still_stopping_clusters = [
            cluster['DBClusterIdentifier'] for cluster in clusters['DBClusters']
            if namespace in cluster['DBClusterIdentifier'] and cluster['Status'] != 'stopped'
        ]
        print("Waiting RDS {namespace} to be stopped...".format(namespace=namespace))
        stopped = not still_stopping_clusters
