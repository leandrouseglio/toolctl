# -*- coding: utf-8 -*-
"""De-isolate pod command."""

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

from metamorphctl.utils.kubeutils import (ISOLATION_LABEL_KEY, is_pod_isolated, load_kubernetes,
                                          remove_isolate_rule_from_network_policies,
                                          remove_label_from_pod, remove_network_policy)
from metamorphctl.utils.printutils import print_error, print_success


@click.command()
@click.option('--pod', '-p', 'pod_name', required=True)
@click.option('--namespace', '-n', required=True)
def cli(pod_name, namespace):
    """De-isolate a kubernetes pod from the network."""
    load_kubernetes()

    try:
        print("Read pod: {} in namespace: {}".format(pod_name, namespace))
        pod = client.CoreV1Api().read_namespaced_pod(name=pod_name, namespace=namespace)
        if not is_pod_isolated(pod):
            print_success("Pod is already de-isolated")
            return

        remove_label_from_pod(pod, ISOLATION_LABEL_KEY)
        remove_isolate_rule_from_network_policies(pod)
        network_policy_name = "{}-deny-all".format(pod.metadata.name)
        print("Remove deny all network policy: {}".format(network_policy_name))
        remove_network_policy(pod.metadata.namespace, network_policy_name)

        print_success("Pod has been de-isolated")
    except ApiException as ex:
        print_error("Error: {} ({})".format(ex.reason, ex.status))
