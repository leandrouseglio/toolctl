# -*- coding: utf-8 -*-
"""Force init command."""

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

# pylint: disable=cyclic-import
from metamorphctl.utils.printutils import print_error, print_success

from .kernels.k8s_certified import K8sCertifiedOperator

AVAILABLE_KERNEL_OPERATORS = {"k8s:certified": K8sCertifiedOperator}


@click.command()
@click.option(
    '--onkernel',
    '-o',
    type=click.Choice(['k8s:certified']),
    default='k8s:certified',
    help='Kernel type')
@click.option('--kernel_namespace', '-k', required=True, help='Kernel namespace')
@click.option('--key', '-u', required=True, help='AWS Key')
@click.option('--secret', '-s', required=True, help='AWS Secret')
@click.option('--region', '-r', required=True, help='AWS Region')
@click.pass_context
def cli(ctx, onkernel, kernel_namespace, key, secret, region):
    """Force kernel initialization command.

    Useful when you are having trouble initializating a kernel through `metamorphctl shellinit`
    """
    try:
        print_success("Initializing kernel: {}".format(kernel_namespace))
        kernel_operator = AVAILABLE_KERNEL_OPERATORS.get(onkernel)
        operator = kernel_operator(ctx.obj, kernel_namespace, key, secret, region)
        operator.initialize()
        print_success("Validating kernel")
        if not operator.validate():
            print_error("Kernel validation failed")
            ctx.abort()
        print_success("Kernel was initialized properly")
    except Exception:  # pylint: disable=broad-except
        print_error("There was a problem initializating the kernel")
        raise
