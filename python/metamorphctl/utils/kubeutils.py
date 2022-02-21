# -*- coding: utf-8 -*-
"""Kubernetes utils."""

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

from time import sleep
import json

from jinja2 import Template
from kubernetes import client, config
from kubernetes.client.models import V1Taint
from kubernetes.client.rest import ApiException

from metamorphctl.cli import pass_environment

ISOLATION_LABEL_KEY = 'isolated'

# kubernetes interfaces where we can find list APIs
K8S_INTERFACES = [
    'AdmissionregistrationV1beta1Api', 'ApiextensionsV1beta1Api', 'ApiregistrationV1Api',
    'AppsV1Api', 'AppsV1beta1Api', 'AppsV1beta2Api', 'AuditregistrationV1alpha1Api',
    'AutoscalingV1Api', 'AutoscalingV2beta1Api', 'AutoscalingV2beta2Api', 'BatchV1Api',
    'BatchV1beta1Api', 'BatchV2alpha1Api', 'CertificatesV1beta1Api', 'CoordinationV1Api',
    'CoordinationV1beta1Api', 'CoreV1Api', 'CustomObjectsApi', 'EventsV1beta1Api',
    'ExtensionsV1beta1Api', 'LogsApi', 'NetworkingV1Api', 'NetworkingV1beta1Api', 'NodeV1alpha1Api',
    'NodeV1beta1Api', 'PolicyV1beta1Api', 'RbacAuthorizationV1Api', 'SchedulingV1beta1Api',
    'StorageV1alpha1Api', 'StorageV1Api', 'StorageV1beta1Api', 'SettingsV1alpha1Api'
]


class SelectorOperator():
    """Available selector operators based on kubernetes documentation."""

    IN = 'In'
    NOT_IN = 'NotIn'
    EXISTS = 'Exists'
    DOES_NOT_EXIST = 'DoesNotExist'


class SelectorParser():
    """Utility class to find objects matching selector.

    For example which NetworkPolicies are being applied to a POD.
    """

    def __init__(self, selector):
        """Init."""
        self.requirements = self._build_generic_selector(selector)

    def _build_generic_selector(self, selector):
        # pylint: disable=no-self-use
        # https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

        req = []
        if selector.match_labels:
            for key, value in selector.match_labels.items():
                # a label selector can be converted into a requirement
                req.append(
                    client.V1LabelSelectorRequirement(
                        key=key, operator=SelectorOperator.IN, values=[value]))

        if selector.match_expressions:
            for expression in selector.match_expressions:
                if isinstance(expression, client.V1LabelSelectorRequirement):
                    req.append(expression)
                else:
                    raise ValueError('Expression type is [{}] but it is expected to '
                                     'be [V1LabelSelectorRequirement]'.format(type(expression)))

        return req

    def _requirement_matches_labels(self, requirement, labels):
        # pylint: disable=no-self-use
        # pylint: disable=no-else-return
        if requirement.operator == SelectorOperator.IN:
            if requirement.key not in labels:
                return False
            return labels[requirement.key] in requirement.values
        elif requirement.operator == SelectorOperator.NOT_IN:
            if requirement.key not in labels:
                return True
            return labels[requirement.key] not in requirement.values
        elif requirement.operator == SelectorOperator.EXISTS:
            return requirement.key in labels
        elif requirement.operator == SelectorOperator.DOES_NOT_EXIST:
            return requirement.key not in labels

        raise ValueError('Requirement operator [{}] not found'.format(requirement.operator))

    def matches(self, labels):
        """Validate if the provided labels are fullfiled by the requirements."""
        for req in self.requirements:
            if not self._requirement_matches_labels(req, labels):
                return False
        # Only return True in case all the requirements are fullfiled
        return True


@pass_environment
def load_kubernetes(env=None):
    """Load kubernetes based on its configuration."""
    try:
        # If kubeconfig is in environment use it, otherwise default to system
        kubeconfig = getattr(env, 'kubeconfig', None)
        config.load_kube_config(config_file=kubeconfig)
    except TypeError:
        print("There was a problem loading kubernetes configuration.\n"
              "Please check that you have initialized a kubernetes environment.\n"
              "You can use the command `metamorphctl shellinit`")
        raise


def is_pod_isolated(pod):
    """Check if pod is isolated."""
    pod_labels = pod.metadata.labels
    isolation_label_value = pod.metadata.name
    return (ISOLATION_LABEL_KEY in pod_labels
            and pod_labels[ISOLATION_LABEL_KEY] == isolation_label_value)


def add_label_to_pod(pod, label_key, label_value):
    """Remove the given label to pod."""
    print("Add label to pod: {}={}".format(label_key, label_value))
    pod_labels = pod.metadata.labels
    pod_labels[label_key] = label_value
    body = {"metadata": {"labels": pod_labels}}
    client.CoreV1Api().patch_namespaced_pod(
        name=pod.metadata.name, namespace=pod.metadata.namespace, body=body)


def remove_label_from_pod(pod, label_key):
    """Remove the given label key from pod."""
    print("Remove pod label: {}".format(label_key))
    pod_labels = pod.metadata.labels
    if label_key in pod_labels:
        # Weird API, you need to set it as None so that the label gets removed
        pod_labels[label_key] = None
        body = {"metadata": {"labels": pod_labels}}
        client.CoreV1Api().patch_namespaced_pod(
            name=pod.metadata.name, namespace=pod.metadata.namespace, body=body)


def exclude_pod_from_network_policies(pod):
    """Exclude the pod from its network policies."""
    isolation_label_value = pod.metadata.name
    add_label_to_pod(pod, ISOLATION_LABEL_KEY, isolation_label_value)

    matched_np = find_pod_network_policies(pod)
    for netpolicy in matched_np:
        print("Exclude pod from network policy: {}".format(netpolicy.metadata.name))
        # exclude target pod from the network policy
        exclude_requirement = client.V1LabelSelectorRequirement(
            key=ISOLATION_LABEL_KEY,
            operator=SelectorOperator.NOT_IN,
            values=[isolation_label_value])
        pod_selector = netpolicy.spec.pod_selector
        if not pod_selector.match_expressions:
            pod_selector.match_expressions = []
        pod_selector.match_expressions.append(exclude_requirement)
        body = {"spec": {"podSelector": pod_selector}}
        client.NetworkingV1Api().patch_namespaced_network_policy(
            name=netpolicy.metadata.name, namespace=netpolicy.metadata.namespace, body=body)


def render_network_policy(pod, network_policy_template):
    """Render a network policy template based on pod."""
    isolation_label_value = pod.metadata.name
    deny_all_np = Template(network_policy_template)
    return deny_all_np.render(
        name=pod.metadata.name,
        selector_key=ISOLATION_LABEL_KEY,
        selector_value=isolation_label_value)


def apply_network_policy(namespace, network_policy_json):
    """Apply the provided network policy."""
    body = json.loads(network_policy_json)
    client.ExtensionsV1beta1Api().create_namespaced_network_policy(namespace=namespace, body=body)


def remove_network_policy(namespace, network_policy_name):
    """Remove the network policy based on the given policy name."""
    client.ExtensionsV1beta1Api().delete_namespaced_network_policy(
        namespace=namespace, name=network_policy_name)


def remove_isolate_rule_from_network_policies(pod):
    """Remove isolate rule if any from the pod's network policies."""
    isolation_label_value = pod.metadata.name
    matched_np = find_pod_network_policies(pod)
    for netpolicy in matched_np:
        pod_selector = netpolicy.spec.pod_selector
        if pod_selector.match_expressions:
            exclude_requirement = client.V1LabelSelectorRequirement(
                key=ISOLATION_LABEL_KEY,
                operator=SelectorOperator.NOT_IN,
                values=[isolation_label_value])
            if exclude_requirement in pod_selector.match_expressions:
                print("Rmove isolate rule in network policy: {}".format(netpolicy.metadata.name))
                pod_selector.match_expressions.pop(
                    pod_selector.match_expressions.index(exclude_requirement))
                body = {"spec": {"podSelector": pod_selector}}
                client.NetworkingV1Api().patch_namespaced_network_policy(
                    name=netpolicy.metadata.name, namespace=netpolicy.metadata.namespace, body=body)


def find_pod_network_policies(pod):
    """Find pod's network policies and return them."""
    network_policies = client.NetworkingV1Api().list_namespaced_network_policy(
        namespace=pod.metadata.namespace)
    matched_np = []
    for netpolicy in network_policies.items:
        selector = SelectorParser(netpolicy.spec.pod_selector)
        if selector.matches(pod.metadata.labels):
            matched_np.append(netpolicy)
    return matched_np


def find_api_in_kubernetes(api_name):
    """Find api by name in the kubernetes library and return it."""
    for interface in K8S_INTERFACES:
        interface_obj = getattr(client, interface, None)
        if interface_obj is not None:
            method_obj = getattr(interface_obj(), api_name, None)
            if method_obj is not None:
                return method_obj
    # Only raise in the case the api couldn't be found in any k8s interface
    raise AttributeError("Could not find: {} in kubernetes library".format(api_name))


def exist_node(node_name):
    """Validate if the given node_name exists in kubernetes."""
    try:
        node = client.CoreV1Api().read_node(name=node_name)
        return bool(node)
    except Exception:  # pylint: disable=broad-except
        return False


def taint_nodes():
    """Taint nodes with start_stop taint and wait for the kube-system pods.

    If the node already had taints, the start_stop one is appended to avoid losing them.
    """
    kube_core_client = client.CoreV1Api()
    retries = 15
    tainted = False
    for i in range(retries):
        try:
            nodes = kube_core_client.list_node().items
            taint = V1Taint(key='start_stop', value='test', effect='NoExecute')
            for node in nodes:
                print('Patching node {}'.format(node.metadata.name))
                new_taints = [taint]
                if node.spec.taints:
                    new_taints += list(
                        filter(lambda taint: taint.key != "start_stop", node.spec.taints))
                taint_patch = {
                    "spec": {
                        "taints": new_taints
                    }
                }
                kube_core_client.patch_node(node.metadata.name, taint_patch)
            tainted = True
            break
        except ApiException as ex:
            print('Nodes could not be tainted: {}. Retrying {}/{}'.format(ex.reason, i, retries))
            print('Patch exception details: {}'.format(ex.body))
            print('Trying to untaint nodes of start_stop taint if they have it.')
            untaint_nodes()
            sleep(10)
    if not tainted:
        raise RuntimeError('Nodes could not be tainted.')
    print("DONE")


def untaint_nodes():
    """Remove start_stop taint from nodes.

    If the node already had taints, the start_stop one is removed keeping the other ones.
    """
    kube_core_client = client.CoreV1Api()
    retries = 15
    untainted = False
    for i in range(retries):
        try:
            nodes = kube_core_client.list_node().items
            for node in nodes:
                print('Patching node {}'.format(node.metadata.name))
                new_taints = []
                if node.spec.taints and len(node.spec.taints) > 1:
                    new_taints = list(
                        filter(lambda taint: taint.key != "start_stop", node.spec.taints))
                taint_patch = {
                    "spec": {
                        "taints": new_taints
                    }
                }
                kube_core_client.patch_node(node.metadata.name, taint_patch)
            untainted = True
            break
        except ApiException as ex:
            print('Nodes could not be untainted: {}. Retrying {}/{}'.format(ex.reason, i, retries))
            print('Patch exception details: {}'.format(ex.body))
            sleep(30)
    if not untainted:
        raise RuntimeError('Nodes could not be untainted.')
    print("DONE")
