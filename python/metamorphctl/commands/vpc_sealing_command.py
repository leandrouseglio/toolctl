# -*- coding: utf-8 -*-
"""VPC sealing command."""

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

from metamorphctl.utils.printutils import confirm, print_success, print_warn

from .vpc_sealing.allow_all_operation import AllowAllOperation
from .vpc_sealing.deny_all_operation import DenyAllOperation
from .vpc_sealing.deny_by_exception_operation import DenyByExceptionOperation
from .vpc_sealing.operation_util import OperationUtil
from .vpc_sealing.permit_by_exception_operation import \
    PermitByExceptionOperation

AVAILABLE_OPERATIONS = {
    "permit-by-exception": PermitByExceptionOperation,
    "allow-all": AllowAllOperation,
    "deny-all": DenyAllOperation,
    "deny-by-exception": DenyByExceptionOperation
}


@click.command()
@click.option(
    '--operation',
    type=click.Choice(['allow-all', 'deny-by-exception', 'deny-all', 'permit-by-exception']),
    required=True)
@click.option('--vpc_id', required=True)
def cli(operation, vpc_id):
    """Seal the VPC. DO NOT USE WITH AWS EKS DEPLOYMENTS.."""
    print_warn("DO NOT USE WITH AWS EKS DEPLOYMENTS (they're not supported yet).")

    func = AVAILABLE_OPERATIONS.get(operation, None)
    operator = func(OperationUtil(vpc_id))
    print(operator.describe())
    confirm("Are you sure to perform this operation?")  # noqa
    operator.apply()
    print_success("OPERATION WAS SUCCESFULLY EXECUTED.")
