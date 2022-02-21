# -*- coding: utf-8 -*-
"""Node drain command."""

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

import subprocess
from subprocess import PIPE, CalledProcessError

import click

from metamorphctl.utils.printutils import confirm, print_error, print_success

# 600 sec = 10 min
TIMEOUT = '600s'


@click.command()
@click.option('--node', '-n', required=True, help='name of the kubernetes node')
def cli(node):
    """Drain the given kubernetes node."""
    try:
        print("Working with the node: {}".format(node))
        confirm("Are you sure to drain the node?")  # noqa

        # The drain command is not available in the kubernetes python library
        # See: https://github.com/kubernetes-client/python/issues/188
        # Let's rely on the underlying `kubectl` command
        print('Waiting up to {} seconds for the node {} to be drained'.format(TIMEOUT, node))
        cmd = [
            'kubectl', 'drain', node, '--ignore-daemonsets', '--delete-local-data', '--force',
            '--timeout', TIMEOUT
        ]
        subprocess.run(cmd, stdout=PIPE, stderr=PIPE, check=True)
        print_success("Node was drained successfully")
    except CalledProcessError as ex:
        print_error("There was a problem draining the node:\n{}".format(ex.stderr))
        raise
    except Exception as ex:  # pylint: disable=broad-except
        print("Exception been caught, error:", ex)
        raise
