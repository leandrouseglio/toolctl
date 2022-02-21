# -*- coding: utf-8 -*-
"""EKS command."""

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

from metamorphctl.utils.printutils import confirm, print_success

from .eks_cluster import start_eks_operation, stop_eks_operation

AVAILABLE_OPERATIONS = {"stop": stop_eks_operation, "start": start_eks_operation}


@click.command()
@click.option('--action', '-a', type=click.Choice(['stop', 'start']), required=True)
@click.option('--rds/--no-rds', default=True)
@click.option('--kernel_namespace', '-k', required=True, envvar='KERNEL_NAMESPACE')
def cli(action, kernel_namespace, rds):
    """Execute an action in a AWS EKS environment."""
    print_success("Working on kernel namespace: {}".format(kernel_namespace))
    operator = AVAILABLE_OPERATIONS.get(action)
    print(operator.describe())
    confirm("Are you sure to perform this action?")  # noqa
    operator.apply(kernel_namespace, rds)
    print_success("Operation was successfully executed")
