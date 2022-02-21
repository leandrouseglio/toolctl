# -*- coding: utf-8 -*-
"""Kernel k8s:certified operator."""

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
import tempfile

import boto3
from jinja2 import Template
from kubernetes import client

from metamorphctl.utils.kubeutils import load_kubernetes

# Template from https://docs.aws.amazon.com/eks/latest/userguide/create-kubeconfig.html
KUBECONFIG_TEMPLATE = '''apiVersion: v1
clusters:
- cluster:
    server: {{ server }}
    certificate-authority-data: {{ certificate }}
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: aws
  name: aws
current-context: aws
kind: Config
preferences: {}
users:
- name: aws
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1alpha1
      command: aws-iam-authenticator
      args:
      - token
      - -i
      - {{ namespace }}
'''


class K8sCertifiedOperator():
    """Operator for k8s:certified."""

    def __init__(self, env, kernel_namespace, key, secret, region):
        """Init."""
        self.env = env
        self.kernel_namespace = kernel_namespace
        self.key = key
        self.secret = secret
        self.region = region

    def initialize(self):
        """Initialize the kernel."""
        # Export necessary variables for other commands
        os.environ['KERNEL_NAMESPACE'] = self.kernel_namespace
        # AWS variables to allow kubernetes authenticate with EKS through aws-iam-authenticator
        os.environ['AWS_ACCESS_KEY_ID'] = self.key
        os.environ['AWS_SECRET_ACCESS_KEY'] = self.secret
        os.environ['AWS_DEFAULT_REGION'] = self.region

        eks = boto3.client('eks')

        cluster = eks.describe_cluster(name=self.kernel_namespace)
        certificate = cluster["cluster"]["certificateAuthority"]["data"]
        server = cluster["cluster"]["endpoint"]
        kubeconfig = Template(KUBECONFIG_TEMPLATE).render(
            server=server, certificate=certificate, namespace=self.kernel_namespace)

        # write kubeconfig to the file /tmp/[namespace]. Overrides if file exists.
        kubeconfig_file = _get_kubeconfig_file(self.kernel_namespace)
        with open(kubeconfig_file, 'w+') as file:
            file.write(kubeconfig)

        self.env.kubeconfig = kubeconfig_file

    # pylint: disable=no-self-use
    def validate(self):
        """Validate the kernel."""
        if not _validate_aws() or not _validate_kubernetes():
            return False
        return True


def _get_kubeconfig_file(namespace):
    """Get the kubeconfig file location for the provided namespace."""
    return os.path.join(tempfile.gettempdir(), namespace)


def _validate_aws():
    """Test with a simple AWS API."""
    try:
        iam_client = boto3.client('iam')
        iam_client.get_user()
        return True
    except Exception:  # pylint: disable=broad-except
        return False


def _validate_kubernetes():
    """Test with a simple Kubernetes API."""
    try:
        load_kubernetes()
        client.CoreV1Api().list_namespace()
        return True
    except Exception:  # pylint: disable=broad-except
        return False
