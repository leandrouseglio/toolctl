# -*- coding: utf-8 -*-
"""Handler."""

# MCAFEE CONFIDENTIAL
# Copyright © 2020 McAfee LLC.
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

import json

import jmespath
import xlsxwriter

from metamorphctl.utils.printutils import print_success
from metamorphctl.commands.inventory.report_handlers.jmespath_custom import CustomFunctions

JMESPATH_OPT = jmespath.Options(custom_functions=CustomFunctions())


def handle(name, config, output):  # pragma: no cover
    """Handle excel report."""
    workbook_name = '{}.xlsx'.format(name)
    workbook = xlsxwriter.Workbook(workbook_name)

    for cfg in config:
        # Include it in the report by default unless `report` is defined with false
        if cfg.get('report', True):
            _handle_item(workbook, cfg, output[cfg['title']])

    workbook.close()
    print_success("Excel report available at {}".format(workbook_name))


def _handle_item(workbook, cfg, item):  # pragma: no cover
    # pylint: disable=too-many-branches
    worksheet = workbook.add_worksheet(cfg['title'])

    header = []
    for field in cfg['fields']:
        if isinstance(field, str):
            header.append({"header": field})
        else:
            header.append({"header": list(field.keys())[0]})

    rows = []
    for subitem in item:
        row = []
        for field in cfg['fields']:
            if isinstance(field, str):
                val = jmespath.search(field, subitem, options=JMESPATH_OPT)
            else:
                val = jmespath.search(list(field.values())[0], subitem, options=JMESPATH_OPT)
            row.append(_parse_value(val))
        rows.append(row)

    # Add a fake row in case no resources were found
    # Otherwise the excel table will fail with errors
    if not rows:
        rows.append(['Empty'] * len(header))
    worksheet.set_column(0, len(header) - 1, 40)  # column length
    worksheet.add_table(0, 0, len(rows), len(header) - 1, {'data': rows, 'columns': header})


def _parse_value(val):  # pragma: no cover
    # If it is an string, just return it
    if isinstance(val, str):
        return val
    # Otherwise, try json parsing, but if fail, return its string representation
    try:
        return json.dumps(val, indent=4)
    except Exception:  # pylint: disable=broad-except
        return str(val)
