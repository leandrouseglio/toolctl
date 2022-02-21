# -*- coding: utf-8 -*-
"""Node isolate command."""

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

from metamorphctl.cli import pass_environment
from metamorphctl.utils.kubeutils import exist_node, load_kubernetes
from metamorphctl.utils.printutils import confirm, print_error, print_success, print_warn

from . import node_drain_command, node_snapshot_command, node_terminate_command


@click.command()
@click.option('--node', '-n', required=True, help='name of the kubernetes node')
@pass_environment
@click.pass_context
def cli(ctx, env, node):
    """Isolate the given kubernetes node.

    It will snapshot, drain and teminate the node.
    """
    try:
        load_kubernetes()
        if not exist_node(node):
            print_error("Node {} was not found in kubernetes".format(node))
            return

        print("Working with the node: {}".format(node))
        print_warn("An snapshot will be taken from the node, it will be drained and terminated.")
        confirm("Are you sure to isolate the node?")  # noqa

        # As user accepted the operation, let's change autoconfirm to True
        # so further commands don't ask for confirmation again.
        env.autoconfirm = True

        print_warn("=== Taking an snapshot from the node ===")
        ctx.invoke(node_snapshot_command.cli, node=node)
        print_warn("=== Draining the node ===")
        ctx.invoke(node_drain_command.cli, node=node)
        print_warn("=== Terminating the node ===")
        ctx.invoke(node_terminate_command.cli, node=node)
        print_success("Node was isolated successfully")

    except Exception as ex:  # pylint: disable=broad-except
        print("Exception been caught, error:", ex)
        raise
