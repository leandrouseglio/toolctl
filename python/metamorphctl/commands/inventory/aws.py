# -*- coding: utf-8 -*-
"""AWS collector."""

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

import os
import boto3
import jmespath

from metamorphctl.utils.config import Config
from metamorphctl.commands.inventory.report_handlers.jmespath_custom import CustomFunctions

from .aws_handlers.asg import Asg
from .aws_handlers.ecr import Ecr
from .aws_handlers.eks import Eks
from .aws_handlers.iam import Iam
from .aws_handlers.resource_tag import ResourceTag
from .aws_handlers.route53 import Route53

AVAILABLE_HANDLERS = {
    "ResourceTagMappingList": ResourceTag,
    "Iam": Iam,
    "Route53": Route53,
    "Asg": Asg,
    "Ecr": Ecr,
    "Eks": Eks
}

JMESPATH_OPT = jmespath.Options(custom_functions=CustomFunctions())


class Aws():
    """Class to handle AWS resources."""

    def __init__(self):
        """Init."""
        self.kernel_ns = os.environ.get("KERNEL_NAMESPACE", None)
        if not self.kernel_ns:
            raise ValueError("KERNEL_NAMESPACE env variable is not present. "
                             "Remember, this command is meant to be run from a "
                             "shell-init'ed terminal.")

        self.handlers = {}
        requested_handlers = Config().get("inventory").get("aws")
        print("Available aws handlers={}, requested={}".format(AVAILABLE_HANDLERS.keys(),
                                                               requested_handlers))
        for handler in requested_handlers & AVAILABLE_HANDLERS.keys():
            self.handlers[handler] = AVAILABLE_HANDLERS[handler](self.kernel_ns)

    def collect(self):
        """Collect data from registered handlers."""
        response = {}
        for key, value in self.handlers.items():
            try:
                response[key] = value.handle()
            except Exception as err:  # pylint: disable=broad-except
                print("Exception been caught, error:", err)
                response[key] = {'error': str(err)}
        return response


class Awsv2():  # pragma: no cover
    """Class to handle AWS resources."""

    def __init__(self):
        """Init."""

    def collect(self):  # pylint: disable=no-self-use
        """Collect AWS data."""
        response = {}
        try:
            aws_cfg = Config().get("inventory").get("awsv2")
            for req in aws_cfg:
                title = req['title']
                print('Collecting AWS: {}'.format(title))
                res = _handle_request(req)
                response[title] = res
        except Exception as err:  # pylint: disable=broad-except
            print("Exception been caught, error:", err)
            response[title] = {'error': str(err)}
        return response


def _handle_request(req):  # pragma: no cover
    """Handle collection of items."""
    res = []
    client = boto3.client(req['service'])

    # if paginator is not supported for the service, execute the api directly
    if req.get('paginator_support') is False:
        out = getattr(client, req['api'])()
        res += jmespath.search(req['objects'] + "[]", out, options=JMESPATH_OPT)
    else:
        paginator = client.get_paginator(req['api'])
        # use params if they are present
        if req.get('params'):
            iterator = paginator.paginate(**req['params'])
        else:
            iterator = paginator.paginate()
        for page in iterator:
            res += jmespath.search(req['objects'] + "[]", page, options=JMESPATH_OPT)

    return res
