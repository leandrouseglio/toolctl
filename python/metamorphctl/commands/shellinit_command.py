# -*- coding: utf-8 -*-
"""Shellinit command."""

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

from os import chdir, getcwd, system
from os.path import basename, exists, expanduser
from shutil import copy

import click

from metamorphctl.utils.printutils import (print_error, print_success, print_warn)


class Cd:
    """Change current directory."""

    def __init__(self, new_path):
        """Initialize the class."""

        self.new_path = expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        """Save the current dir, change it by the new."""

        self.saved_path = getcwd()
        chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        """Restory the saved directory."""

        chdir(self.saved_path)


@click.command()
@click.option('--bind', '-b', required=True, help='Path to kubernetes bind file')
@click.option(
    '--onkernel',
    '-o',
    type=click.Choice(['k8s:certified', 'k8s:certified-pks-fedramp']),
    default='k8s:certified',
    help='Kernel type')
@click.option('--key', '-u', required=True, help='AWS Key')
@click.option('--secret', '-s', required=True, help='AWS Secret')
def cli(bind, onkernel, key, secret):
    """Initialize a metamorph environment.

    i.e: metamorphctl shellinit --bind kernel.bind.k8s-certified.mcaro.cfg
                                --key AKI...IQ --secret h3L...gGJ
    """
    if not exists(bind):
        print_error('Bind file does not exist: {}'.format(bind))
        return

    kernel_bind_base_name = basename(bind)
    cleanup_cmds = [
        """docker ps -a -q """
        """--filter """
        """ancestor="""
        """artifactory-lvs.corpzone.internalzone.com:6565"""
        """/metamorph/ubuntu_runner"""
        """ | (xargs -I '{}' docker kill {}  > /dev/null 2>&1 )""", "sudo pkill -f monitor_portfw",
        "sudo pkill -f monitor_portfw_registry", "sudo pkill -f monitor_proxy",
        """sudo pkill -f "kubectl proxy" """, "sudo pkill -f kubectl_orig", "rm -rf .shellinit",
        "mkdir .shellinit"
    ]

    print_success("Cleaning up the environments")
    for cmd in cleanup_cmds:
        system(cmd)  # nosec

    shellinit_preparation_cmds = [
        """echo "service_name: .kernel" > .service""", "mkdir tools", "mkdir kernel", "mkdir certs"
    ]

    print_success("Preparing shellinit")
    copy(bind, ".shellinit")
    with Cd(".shellinit"):
        for cmd in shellinit_preparation_cmds:
            system(cmd)  # nosec

        print_success("Runnning metamorph shellinit")
        shellinit_cmd = ("""metamorph shellinit """
                         """--options={kernel_bind_base_name},"""
                         """ACCESS_KEY={key},"""
                         """SECRET_KEY={secret}"""
                         """ --onkernel={onkernel}""")\
            .format(onkernel=onkernel,
                    key=key,
                    secret=secret,
                    kernel_bind_base_name=kernel_bind_base_name)
        system(shellinit_cmd)  # nosec
        print_warn("Check that the shellinit works, and take into acount that "
                   ""
                   """THIS MACHINE USES BY DEFAULT THE KERNEL NAMESPACE""")
