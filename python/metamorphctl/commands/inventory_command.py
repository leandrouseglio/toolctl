# -*- coding: utf-8 -*-
"""Inventory command."""

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

import datetime
import json
import os
from importlib import import_module

import click
from ruamel import yaml

from metamorphctl.utils.config import Config
from metamorphctl.utils.printutils import print_success, print_warn
from metamorphctl.commands.inventory.report_handlers import excel

OUTPUT_FORMATS = {
    "json": lambda c, s: json.dump(c, s, indent=2, default=str),
    "yaml": yaml.round_trip_dump
}

REPORT_HANDLERS = {
    "excel": excel,
}


@click.command()
@click.option('--systems', default='awsv2,kubernetes')
@click.option('--output', type=click.Choice(['json', 'yaml']), default='json')
@click.option('--file')
@click.option(
    '--report',
    type=click.Choice(['excel']),
    default=None,
    help='summary report in the specified format')
def cli(systems, output, file=None, report=None):
    """Write an inventory of the system."""
    collectors = _build_collectors(systems, Config().get("inventory").keys())
    items = {}
    for col in collectors:
        try:
            name = col["name"]
            print_warn("Running collector: {}".format(name))
            items[col["name"]] = col["instance"].collect()
            if report:
                print_warn("Generating report for: {}. Please wait.".format(name))
                now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%S")
                filename = "{}_report-{}".format(name, now)
                cfg = Config().get("inventory").get(name)
                REPORT_HANDLERS[report].handle(filename, cfg, items[name])
        except Exception as err:  # pylint: disable=broad-except
            print("Exception been caught, error:", err)
            items[col["name"]] = {'error': str(err)}

    _write_output(output, file, {
        "dateUtc": datetime.datetime.utcnow().isoformat(),
        "systems": items
    })


def _build_collectors(requested_collectors, available_collectors):
    """Build collectors from config."""
    requested_collectors = available_collectors \
        if requested_collectors == "all" \
        else requested_collectors.split(",")
    print("Available collectors={}, requested={}".format(available_collectors,
                                                         requested_collectors))
    classes = []
    module_object = import_module("metamorphctl.commands.inventory")
    for key in requested_collectors & available_collectors:
        classes.append({"name": key, "instance": getattr(module_object, key.title())()})
    return classes


def _write_output(output, file, content):
    report_dumper = OUTPUT_FORMATS.get(output, OUTPUT_FORMATS["json"])
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H_%M_%S")
    file = file if file else os.path.join(
        os.getcwd(), "inventory-{date}.{format}".format(date=now, format=output))
    with open(file, 'w', encoding='utf-8') as stream:
        report_dumper(content, stream)
    print_success("Full inventory output available at {}".format(file))
