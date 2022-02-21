# -*- coding: utf-8 -*-
"""Node snapshot command."""

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

from datetime import datetime

import boto3
import click

from metamorphctl.utils.awsutils import find_ec2_instance
from metamorphctl.utils.printutils import confirm, print_success

# 15 * 40 = 600 sec = 10 min (boto3 default)
WAIT_DELAY_SEC = 15
WAIT_ATTEMPTS = 40


@click.command()
@click.option('--node', '-n', required=True, help='ip, dns or instanceId')
def cli(node):
    """Create an snapshot from the given node."""
    try:
        ec2_instance = find_ec2_instance(node)
        if not ec2_instance:
            print('Could not find EC2 instance: {}'.format(node))
            return

        instance_id = ec2_instance['InstanceId']
        instance_name = next((e['Value'] for e in ec2_instance['Tags'] if e['Key'] == 'Name'), None)
        print('EC2 instance: {} ({})'.format(instance_id, instance_name))
        confirm("Are you sure to create an image from this instance?")  # noqa
        _create_ec2_image(ec2_instance)
    except Exception as ex:  # pylint: disable=broad-except
        print("Exception been caught, error:", ex)
        raise


def _create_ec2_image(ec2_instance):
    ec2 = boto3.client('ec2')
    waiter = ec2.get_waiter('image_available')

    instance_id = ec2_instance['InstanceId']
    image_name = "{}-{}".format(instance_id, datetime.utcnow().strftime('%Y-%m-%dT%H_%M_%S'))
    image = ec2.create_image(InstanceId=instance_id, Name=image_name)
    image_id = image['ImageId']

    print('Waiting up to {} seconds for the image {} to be created'.format(
        WAIT_DELAY_SEC * WAIT_ATTEMPTS, image_name))
    waiter.wait(
        ImageIds=[image['ImageId']],
        WaiterConfig={
            'Delay': WAIT_DELAY_SEC,
            'MaxAttempts': WAIT_ATTEMPTS
        })
    print_success('Image was created successfully: {} ({})'.format(image_id, image_name))
