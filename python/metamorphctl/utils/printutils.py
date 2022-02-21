# -*- coding: utf-8 -*-
"""Utils."""

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


def print_success(msg):
    """Print on console with colored (green) text."""
    click.secho(msg, fg='green', bold=True)


def print_error(msg):
    """Print on console with colored (red) text."""
    click.secho(msg, fg='red', bold=True)


def print_warn(msg):
    """Print on console with colored (yellow) text."""
    click.secho(msg, fg='yellow', bold=True)


@pass_environment
def confirm(env, msg):
    """Request confirmation over console. Do nothing if autoconfirm=True."""
    if not env.autoconfirm:
        click.confirm(msg, abort=True)
