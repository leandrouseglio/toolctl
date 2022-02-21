# -*- coding: utf-8 -*-
"""Isolate pod command."""

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

import click
from kubernetes import client
from kubernetes.client.rest import ApiException

from metamorphctl.utils.kubeutils import apply_network_policy, exclude_pod_from_network_policies, \
    is_pod_isolated, load_kubernetes, render_network_policy

from metamorphctl.utils.printutils import print_error, print_success

NETWORK_POLICY_DENY_ALL = '''{
    "apiVersion": "extensions/v1beta1",
    "kind": "NetworkPolicy",
    "metadata": {
        "name": "{{ name }}-deny-all"
    },
    "spec": {
        "policyTypes": ["Egress", "Ingress"],
        "podSelector": {
            "matchLabels": {
                "{{ selector_key }}": "{{ selector_value }}"
            }
        }
    }
}'''


@click.command()
@click.option('--pod', '-p', 'pod_name', required=True)
@click.option('--namespace', '-n', required=True)
def cli(pod_name, namespace):
    """Isolate a kubernetes pod from the network."""
    load_kubernetes()

    try:
        print("Read pod: {} in namespace: {}".format(pod_name, namespace))
        pod = client.CoreV1Api().read_namespaced_pod(name=pod_name, namespace=namespace)
        if is_pod_isolated(pod):
            print_success("Pod is already isolated")
            return

        exclude_pod_from_network_policies(pod)
        print("Add deny all network policy only for pod: {}".format(pod.metadata.name))
        network_policy_json = render_network_policy(pod, NETWORK_POLICY_DENY_ALL)
        apply_network_policy(pod.metadata.namespace, network_policy_json)

        print_success("Pod has been isolated")
    except ApiException as ex:
        print_error("Error: {} ({})".format(ex.reason, ex.status))
