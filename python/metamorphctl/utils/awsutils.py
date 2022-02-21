# -*- coding: utf-8 -*-
"""AWS utils."""

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

import boto3


def find_ec2_instance(node):
    """Find EC2 instance by instance_id, private ip or private dns."""
    ec2 = boto3.client('ec2')

    by_instance_id = ec2.describe_instances(Filters=[{
        'Name': 'instance-id',
        'Values': [node]
    }])['Reservations']
    if by_instance_id:
        return by_instance_id[0]['Instances'][0]

    by_private_ip = ec2.describe_instances(Filters=[{
        'Name': 'private-ip-address',
        'Values': [node]
    }])['Reservations']
    if by_private_ip:
        return by_private_ip[0]['Instances'][0]

    by_private_dns = ec2.describe_instances(Filters=[{
        'Name': 'private-dns-name',
        'Values': [node]
    }])['Reservations']
    if by_private_dns:
        return by_private_dns[0]['Instances'][0]

    return None
