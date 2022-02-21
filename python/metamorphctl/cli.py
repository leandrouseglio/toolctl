# -*- coding: utf-8 -*-
"""CLI entry point."""

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

from shutil import copyfile

import os
import click


def bootstrap():  # pragma: no cover
    """Bootstrap helper."""
    module_path = os.path.dirname(__file__)
    folder = os.path.join(os.path.expanduser("~"), ".metamorphctl")
    filename = "config.yaml"
    if not os.path.exists(folder):
        os.makedirs(folder)
    if not os.path.exists(os.path.join(folder, filename)):
        # create config file based on the embedded one
        copyfile(os.path.join(module_path, filename), os.path.join(folder, filename))


class Environment():  # pragma: no cover
    """Environment use for the multiple commands."""

    def __init__(self):
        """Init."""
        self.autoconfirm = False


CMD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
# pylint: disable=invalid-name
pass_environment = click.make_pass_decorator(Environment, ensure=True)


class ComplexCLI(click.MultiCommand):  # pragma: no cover
    """Dynamically loads commands from python modules ending with `_command.py`."""

    def list_commands(self, ctx):
        """Build a list with files ending with `_command.py`."""
        commands = []
        for filename in os.listdir(CMD_FOLDER):
            if filename.endswith('_command.py'):
                # foo_command.py => foo
                commands.append(filename[:-11])
        commands.sort()
        return commands

    # pylint: disable=arguments-differ
    # pylint: disable=inconsistent-return-statements
    def get_command(self, ctx, name):
        """Import the python module."""
        try:
            mod = __import__('metamorphctl.commands.' + name + '_command', None, None, ['cli'])
        except ImportError as err:
            print("Command=[{}] cannot be imported due to=[{}]."
                  " Please contact the engineering team.".format(name, err))
            return
        return mod.cli


class RequiredIf(click.Option):  # pragma: no cover
    """Option which is only required if other option/s were provided."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.required_if = kwargs.pop("required_if")
        super(RequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        """Handle options."""
        for required in self.required_if:
            # if required opt is not in provided opts, do not prompt for a value
            if required not in opts:
                self.prompt = None
        return super(RequiredIf, self).handle_parse_result(ctx, opts, args)


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.version_option(message='%(version)s')
@click.option('--autoconfirm/--no-autoconfirm', '-y', default=False)
@click.option('--force_init', '-f', is_flag=True, default=False)
@click.option(
    '--onkernel',
    '-o',
    cls=RequiredIf,
    type=click.Choice(['k8s:certified']),
    prompt=True,
    required_if=['force_init'])
@click.option('--kernel_namespace', '-k', cls=RequiredIf, prompt=True, required_if=['force_init'])
@click.option('--key', '-u', cls=RequiredIf, prompt=True, required_if=['force_init'])
@click.option('--secret', '-s', cls=RequiredIf, prompt=True, required_if=['force_init'])
@click.option('--region', '-r', cls=RequiredIf, prompt=True, required_if=['force_init'])
@pass_environment
@click.pass_context
def cli(ctx, env, autoconfirm, force_init, onkernel, kernel_namespace, key, secret,
        region):  # pragma: no cover
    """Metamorphctl command line interface."""
    bootstrap()

    # pylint: disable=unused-argument
    env.autoconfirm = autoconfirm

    # Convenient kernel initialization in case `metamorphctl shellinit` is not working
    if force_init:
        # Import these here, otherwise they fail importing `metamorphctl.cli.pass_environment`
        # pylint: disable=import-outside-toplevel
        from metamorphctl.commands import forceinit_command_internal
        ctx.invoke(
            forceinit_command_internal.cli,
            onkernel=onkernel,
            kernel_namespace=kernel_namespace,
            key=key,
            secret=secret,
            region=region)
        click.echo("\n=== Executing command: {} ===\n".format(ctx.invoked_subcommand))
