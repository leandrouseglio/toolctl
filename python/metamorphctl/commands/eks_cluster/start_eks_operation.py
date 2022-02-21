# -*- coding: utf-8 -*-
"""Start EKS cluster operation."""

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

from metamorphctl.utils.kubeutils import load_kubernetes, taint_nodes, untaint_nodes
from metamorphctl.utils.printutils import print_success, print_warn
from metamorphctl.utils.timeout import timeout, TimeOutException

KUBE_SYSTEM = 'kube-system'
LEGACY_SKYDNS = 'legacy-skydns'
CLUSTER_AUTOSCALER = 'cluster-autoscaler'
TOLERATION_KEY = 'start_stop'
TOLERATION_YAML = '''
spec:
  template:
    spec:
      tolerations:
      - key: "start_stop"
        operator: Equal
        value: "test"
'''

AUTOSCALING_EKS_PROCESSES = [
    'AddToLoadBalancer', 'AlarmNotification', 'HealthCheck', 'Launch',
    'RemoveFromLoadBalancerLowPriority', 'ReplaceUnhealthy', 'ScheduledActions', 'Terminate'
]


def describe():
    """Describe start eks operation."""
    return "About to start an eks cluster"


def apply(namespace, start_rds):
    """Orchestrate the EKS environment start."""
    load_kubernetes()
    autoscaling_client = boto3.client('autoscaling')
    ec2_client = boto3.client('ec2')
    rds_client = boto3.client('rds')

    print_warn('\n\n== ASG ==\nPausing Kubernetes cluster-autoscaler\n')
    _disable_cluster_autoscaler()

    print_warn('\n\n== Taint k8s Nodes ==\n\n')
    taint_nodes()

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('== Adding tolerations to kube-system and legacy-skydns resources == \n')
    _add_toleration(KUBE_SYSTEM, [CLUSTER_AUTOSCALER])
    _add_toleration(LEGACY_SKYDNS)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('\n\n== Starting Instances ==\n')
    _start_instances(namespace, ec2_client)
    _wait_nodes_readiness(namespace, ec2_client)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    if start_rds:
        print_warn('\n\n== Starting RDS clusters ==\n')
        _start_rds_clusters(namespace, rds_client)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('\n\n== Waiting for etcd cluster ==\n\n')
    _wait_etcd_cluster()

    print("\nWaiting 60 seconds")
    sleep(60)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('\n\n == Untaint k8s nodes ==\nFree the cluster to be used by other services\n')
    untaint_nodes()

    print("\nWaiting 10 seconds")
    sleep(10)

    print_warn('\n\n == Restart Pods ==\nRestart pods after the taint\n')
    _restart_pods([KUBE_SYSTEM, LEGACY_SKYDNS])

    # Wait 10 minutes
    for i in range(10, 0, -1):  # FIXME: we need to check why this wait is needed
        print("\nWaiting {n} minutes before releasing autoscaling groups...".format(n=i))
        sleep(60)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('\n\n== ASG ==\nResuming AutoScaling group\n')
    _resume_autoscaling_group(namespace, autoscaling_client)

    print_warn('\n\n== ASG ==\nResuming Kubernetes cluster-autoscaler\n')
    _enable_cluster_autoscaler()

    # Wait 10 minutes
    for i in range(10, 0, -1):
        print("\nWaiting {n} minutes to give pods time to become ready...".format(n=i))
        sleep(60)

    # Reload to refresh token and prevent 'ApiException (401) [Unauthorized]'
    load_kubernetes()

    print_warn('\n\n == Restart unready Pods ==\nRestart pods that are still unready\n')
    _restart_pods([KUBE_SYSTEM, LEGACY_SKYDNS], only_if_unready=True)

    print_success("DONE\n\n-->{} STARTED!<--".format(namespace))


def _add_toleration(namespace, excludes=None):
    """Add toleration to deployments and stateful sets.

    It uses the toleration data loaded from TOLERATION_YAML
    If it already had tolerations, the start_stop one is appended to avoid losing them.
    """
    kube_apps_client = client.AppsV1Api()
    if not excludes:
        excludes = []
    print('\nGetting deployments, statefull sets and '
          'daemons sets in: {namespace}'.format(namespace=namespace))
    toleration_data = yaml.load(TOLERATION_YAML, Loader=yaml.SafeLoader)

    deployments = kube_apps_client.list_namespaced_deployment(namespace)
    statefull_sets = kube_apps_client.list_namespaced_stateful_set(namespace)
    daemon_set = kube_apps_client.list_namespaced_daemon_set(namespace)
    replica_sets = kube_apps_client.list_namespaced_replica_set(namespace)

    deployments_items = [(item, kube_apps_client.patch_namespaced_deployment)
                         for item in deployments.items]
    stateful_sets_items = [(item, kube_apps_client.patch_namespaced_stateful_set)
                           for item in statefull_sets.items]
    replica_sets_items = [(item, kube_apps_client.patch_namespaced_replica_set)
                          for item in replica_sets.items if not item.metadata.owner_references
                          ]  # This prevents patching RS owned by deployments
    daemon_set_items = [(item, kube_apps_client.patch_namespaced_daemon_set)
                        for item in daemon_set.items
                        if (item.metadata.name in ["aws-node", "kube-proxy"])]
    print('\nAdding toleration to deployments, statefull_sets, replica sets and '
          'daemons sets in {namespace}: '.format(namespace=namespace))
    for item, path_function in (
            deployments_items + stateful_sets_items + daemon_set_items + replica_sets_items):

        if item.metadata.name not in excludes:
            print('Patching {}'.format(item.metadata.name))
            toleration = copy.deepcopy(toleration_data)
            if item.spec.template.spec.tolerations:
                former_tolerations = filter(lambda t: t.key != TOLERATION_KEY,
                                            item.spec.template.spec.tolerations)
                toleration['spec']['template']['spec']['tolerations'] += former_tolerations

            path_function(item.metadata.name, namespace, body=toleration)
        else:
            print('Skipping (because it is excluded) {}'.format(item.metadata.name))


def _restart_pods(exclude_namespaces, only_if_unready=False):
    """Restarts all pods but the ones in the excluded namespaces.

    When the optional `only_if_unready` argument is set to True, it only restart
    pods that are unready (based on its container statuses)
    """
    kube_core_client = client.CoreV1Api()
    pods_list = kube_core_client.list_pod_for_all_namespaces(watch=False)
    pods_list = [pod for pod in pods_list.items if pod.metadata.namespace not in exclude_namespaces]

    for pod in pods_list:
        if only_if_unready and _pod_ready(pod):
            continue

        print("Deleting pod: {pod}, in "
              "namespace: "
              "{namespace}".format(pod=pod.metadata.name, namespace=pod.metadata.namespace))
        try:
            kube_core_client.delete_namespaced_pod(
                pod.metadata.name, pod.metadata.namespace, grace_period_seconds=0)
        except ApiException as ex:
            print('Pod cannot be delete, ignoring error: {}. IGNORING.... '.format(ex.reason))


def _pod_ready(pod):
    """Check if pod is ready.

    A pod is ready when the pod condition status 'ContainersReady' is true.
    More info: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-conditions
    """
    return [c for c in pod.status.conditions if c.type == 'ContainersReady' and c.status == 'True']


def _start_instances(namespace, ec2_client):
    """Start EC2 instances."""
    instance_objects = ec2_client.describe_instances(Filters=[
        {
            'Name': 'tag:KubernetesCluster',
            'Values': [namespace]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['stopped']
        },
    ])
    instances = []
    for reservation in instance_objects['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance['InstanceId'])

    if instances:
        print("Starting cluster {}, instances: {}".format(namespace, instances))
        ec2_client.start_instances(InstanceIds=instances)

        print("Waiting for all the instances being started")
        ec2_client.get_waiter('instance_running').wait(InstanceIds=instances)

        print("DONE")
    else:
        print("No instances to be started, SKIPPING STARTING OF THE INSTANCES")


def _start_rds_clusters(namespace, rds_client):
    """Start the RDS instances."""
    clusters = rds_client.describe_db_clusters()
    print(clusters)
    stopped_clusters = [
        cluster['DBClusterIdentifier'] for cluster in clusters['DBClusters']
        if namespace in cluster['DBClusterIdentifier'] and cluster['Status'] == 'stopped'
    ]

    if stopped_clusters:
        for cluster in stopped_clusters:
            print("Starting cluster {}".format(cluster))
            rds_client.start_db_cluster(DBClusterIdentifier=cluster)
    else:
        print("No clusters to be started, SKIPPING STARTING OF THE RDS INSTANCES")

    print("Waiting for all the clusters being started")
    desired_clusters = [
        cluster['DBClusterIdentifier'] for cluster in clusters['DBClusters']
        if namespace in cluster['DBClusterIdentifier'] and cluster['Status'] != 'available'
    ]
    try:
        _wait_rds_clusters(desired_clusters, rds_client)
    except TimeOutException:
        raise RuntimeError("Timed out waiting for clusters to be available.")


@timeout(1800)  # wait 30 min before failing
def _wait_rds_clusters(desired_clusters, rds_client):
    """Wait until all the RDS clusters are started."""
    while True:
        clusters = rds_client.describe_db_clusters()
        available_clusters = [
            cluster['DBClusterIdentifier'] for cluster in clusters['DBClusters'] if
            cluster['DBClusterIdentifier'] in desired_clusters and cluster['Status'] == 'available'
        ]

        if len(desired_clusters) == len(available_clusters):
            print("All clusters started")
            break

        print("Waiting for clusters to be started {}/{}".format(
            len(available_clusters), len(desired_clusters)))
        sleep(3)
    print("DONE")


def _wait_nodes_readiness(namespace, ec2_client):
    # pylint: disable=too-many-branches
    """Wait for all nodes to be registered and ready."""
    kube_core_client = client.CoreV1Api()
    node_objects = ec2_client.describe_instances(Filters=[
        {
            'Name': 'tag:KubernetesCluster',
            'Values': [namespace]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        },
    ])
    nodes = []
    for reservation in node_objects['Reservations']:
        for node in reservation['Instances']:
            nodes.append(node['PrivateDnsName'])

    print("Waiting for all nodes to be registered: {}".format(nodes))
    while True:
        current_nodes = [i.metadata.name for i in kube_core_client.list_node().items]
        if len(current_nodes) == len(nodes):
            print("All nodes are registered.")
            break
        print("Waiting for all nodes to be registered: {}/{}".format(
            len(current_nodes), len(nodes)))
        sleep(3)
    print("DONE")

    print("Waiting for all nodes to be in Ready state: {}".format(nodes))
    while True:
        ready_nodes = []
        current_nodes = kube_core_client.list_node().items
        for node in current_nodes:
            if list(
                    filter(lambda c: c.type == "Ready" and c.status == "True",
                           node.status.conditions)):
                ready_nodes.append(node)
        if len(ready_nodes) == len(current_nodes):
            print("All nodes are ready: {}/{}".format(len(ready_nodes), len(current_nodes)))
            break
        ready_node_names = [n.metadata.name for n in ready_nodes]
        # pylint: disable=consider-using-set-comprehension
        pending_node_names = list(
            set([n.metadata.name for n in current_nodes]) - set(ready_node_names))
        print("Waiting for all nodes to be ready. Ready: {}. Pending: {}.".format(
            ready_node_names, pending_node_names))
        sleep(3)
    print("DONE")


def _wait_etcd_cluster():
    """Wait for at least 3 pods in the ETCD cluster."""
    print("Deleting old etcd pods to enforce new tolerations")
    _delete_etcd_pods()

    kube_core_client = client.CoreV1Api()
    while True:
        etcd_pods = len(
            kube_core_client.list_namespaced_pod(KUBE_SYSTEM, label_selector='app=etcd').items)
        print("\nWaiting for at least 3 etcd cluster ({}/3)".format(etcd_pods))
        if etcd_pods >= 3:
            break
        sleep(3)
    print("DONE")


def _delete_etcd_pods():
    """Delete all etcd pods from kube-system namespace."""
    kube_core_client = client.CoreV1Api()
    etcd_pods = kube_core_client.list_namespaced_pod(KUBE_SYSTEM, label_selector='app=etcd').items
    for pod in etcd_pods:
        print("Deleting pod: {pod}, in "
              "namespace: "
              "{namespace}".format(pod=pod.metadata.name, namespace=pod.metadata.namespace))
        try:
            kube_core_client.delete_namespaced_pod(
                pod.metadata.name, pod.metadata.namespace, grace_period_seconds=0)
        except ApiException as ex:
            print('Pod cannot be delete, ignoring error: {}. IGNORING.... '.format(ex.reason))


def _resume_autoscaling_group(namespace, autoscaling_client):
    """Resume autoscaling group processes.

    All the processes are resumed but the AZRebalance process.
    """
    paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups')
    page_iterator = paginator.paginate(PaginationConfig={'PageSize': 100})
    auto_scaling_groups = list(
        page_iterator.search(
            "AutoScalingGroups[?contains(Tags[?Key=='KubernetesCluster'].Value,'{}')].[AutoScalingGroupName]".  # noqa
            format(namespace)))
    print("Resuming {} autoscaling groups".format(len(auto_scaling_groups)))
    for group in auto_scaling_groups:
        print("Resuming {}".format(group[0]))
        autoscaling_client.resume_processes(
            AutoScalingGroupName=group[0], ScalingProcesses=AUTOSCALING_EKS_PROCESSES)


def _disable_cluster_autoscaler():
    """Disables cluster-autoscaler deployment scaling it down to 0 replicas."""
    _scale_cluster_autoscaler_deploy(0)


def _enable_cluster_autoscaler():
    r"""Enable cluster-autoscaler deployment scaling it up to 1 replicas.

    The default value for this deployment is one replica.
    More info: https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/\
        cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml#L127
    """
    _scale_cluster_autoscaler_deploy(1)


def _scale_cluster_autoscaler_deploy(replicas):
    """Scales cluster-autoscaler deployment."""
    kube_apps_client = client.AppsV1Api()
    yaml_patch = '''
    spec:
      replicas: {}
    '''.format(replicas)
    patch = yaml.load(yaml_patch, Loader=yaml.SafeLoader)

    try:
        kube_apps_client.patch_namespaced_deployment(CLUSTER_AUTOSCALER, KUBE_SYSTEM, patch)
        print("DONE")
    except ApiException as exc:
        raise RuntimeError("Failed scaling cluster-autoscaler\nCause: {}".format(exc))
