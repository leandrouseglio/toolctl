# -*- coding: utf-8 -*-
"""De-isolate label command."""

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

from metamorphctl.utils.kubeutils import load_kubernetes
from metamorphctl.utils.printutils import confirm, print_error

from . import pod_deisolate_command


@click.command()
@click.option('--label_selector', '-l', required=True)
@click.option('--namespace', '-n', required=True)
@click.pass_context
def cli(ctx, label_selector, namespace):
    """De-isolate kubernetes pods based on label_selector."""
    load_kubernetes()
    try:
        pods = client.CoreV1Api().list_namespaced_pod(
            label_selector=label_selector, namespace=namespace)

        if not pods.items:
            print_error("There is no POD matching label selector: {}".format(label_selector))
            return

        print("PODs matching label_selector: {}".format(label_selector))
        for pod in pods.items:
            print(pod.metadata.name)
        confirm("Are you sure to de-isolate these pods?")  # noqa
        for pod in pods.items:
            ctx.invoke(
                pod_deisolate_command.cli,
                pod_name=pod.metadata.name,
                namespace=pod.metadata.namespace)
    except Exception as ex:  # pylint: disable=broad-except
        print("Exception been caught, error:", ex)
        raise
