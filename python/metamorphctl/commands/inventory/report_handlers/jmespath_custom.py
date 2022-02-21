# -*- coding: utf-8 -*-
"""Custom functions for jmespath."""

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

import boto3
from jmespath import functions


# https://pypi.org/project/jmespath/
class CustomFunctions(functions.Functions):  # pragma: no cover
    """Custom functions for jmespath."""

    # pylint: disable=no-self-use

    @functions.signature({'types': ['string']})
    def _func_aws_ami(self, ami_id):
        client = boto3.client('ec2')
        return client.describe_images(ImageIds=[ami_id])

    @functions.signature({'types': ['string']})
    def _func_aws_attached_policy(self, role_name):
        client = boto3.client('iam')
        return client.list_attached_role_policies(RoleName=role_name)

    @functions.signature({'types': ['array']})
    def _func_aws_policy_document(self, policy):
        client = boto3.client('iam')
        return client.get_policy_version(PolicyArn=policy[0], VersionId=policy[1])

    @functions.signature({'types': ['string']})
    def _func_aws_elb_tags(self, elb_name):
        client = boto3.client('elb')
        return client.describe_tags(LoadBalancerNames=[elb_name])

    @functions.signature({'types': ['string']})
    def _func_aws_elbv2_tags(self, elb_arn):
        client = boto3.client('elbv2')
        return client.describe_tags(ResourceArns=[elb_arn])

    @functions.signature({'types': ['string']})
    def _func_aws_elbv2_listeners(self, elb_arn):
        client = boto3.client('elbv2')
        return client.describe_listeners(LoadBalancerArn=elb_arn)

    @functions.signature({'types': ['string']})
    def _func_aws_s3_location(self, bucket):
        client = boto3.client('s3')
        return client.get_bucket_location(Bucket=bucket)

    @functions.signature({'types': ['string']})
    def _func_aws_s3_lifecycle(self, bucket):
        client = boto3.client('s3')
        try:
            return client.get_bucket_lifecycle(Bucket=bucket)
        except Exception:  # pylint: disable=broad-except
            pass

    @functions.signature({'types': ['string']})
    def _func_aws_s3_versioning(self, bucket):
        client = boto3.client('s3')
        return client.get_bucket_versioning(Bucket=bucket)

    @functions.signature({'types': ['string']})
    def _func_aws_s3_encryption(self, bucket):
        client = boto3.client('s3')
        try:
            return client.get_bucket_encryption(Bucket=bucket)
        except Exception:  # pylint: disable=broad-except
            pass

    @functions.signature({'types': ['string']})
    def _func_aws_s3_public_access_block(self, bucket):
        client = boto3.client('s3')
        try:
            return client.get_public_access_block(Bucket=bucket)
        except Exception:  # pylint: disable=broad-except
            pass

    @functions.signature({'types': ['string']})
    def _func_aws_s3_acl(self, bucket):
        client = boto3.client('s3')
        return client.get_bucket_acl(Bucket=bucket)

    @functions.signature({'types': ['string']})
    def _func_aws_ecr_images(self, repo_name):
        client = boto3.client('ecr')
        return client.list_images(repositoryName=repo_name)

    @functions.signature({'types': ['string']})
    def _func_aws_eks_cluster(self, cluster_name):
        client = boto3.client('eks')
        return client.describe_cluster(name=cluster_name)
