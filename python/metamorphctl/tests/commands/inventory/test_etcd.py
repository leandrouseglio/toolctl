# -*- coding: utf-8 -*-
"""K8s inventory tests."""

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

from unittest import mock

import pytest

from metamorphctl.utils.config import Config
from metamorphctl.commands.inventory.etcd import Etcd


# pylint: disable=unused-argument, missing-docstring
class _Child:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.dir = False

    def get(self, value, default=None):
        return getattr(self, value)

    def __getitem__(self, value):
        return getattr(self, value)


class _DirectoriesMock:
    def __init__(self, children=None, nodes=None, key="/kernel"):
        self._children = children
        self.nodes = nodes
        self.action = 'get'
        self.dir = True
        self.value = None
        self.key = key

    def get(self, value, default=None):
        return getattr(self, value)

    def __getitem__(self, value):
        return getattr(self, value)


def test_collect_etcd_with_empty_env():
    """Test when there is no ETCDCTL_PEERS env variable."""
    with pytest.raises(ValueError):
        Etcd()


@mock.patch.dict('metamorphctl.commands.inventory.etcd.os.environ',
                 {'ETCDCTL_PEERS': 'http://localhost:5555'})
@mock.patch('metamorphctl.commands.inventory.etcd.etcd', autospec=True)
def test_collect_etcd_with_empty_config(etcd):
    """Test when there is no etcd config in config.yaml."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config, \
            pytest.raises(ValueError):
        mocked_config.return_value = {"etcd": []}
        Etcd()


@mock.patch.dict('metamorphctl.commands.inventory.etcd.os.environ',
                 {'ETCDCTL_PEERS': 'http://localhost:5555'})
@mock.patch('metamorphctl.commands.inventory.etcd.etcd', autospec=True)
def test_collect_etcd_with_empty_resources(etcd):
    """Test when there is no etcd resource to collect from."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config:
        mocked_config.return_value = {"etcd": []}
        with pytest.raises(ValueError):
            Etcd().collect()


@pytest.mark.parametrize(
    "etcd_inventory_output, read_side_effect",
    [
        (
            {
                "type": "directory",
                "path": "/kernel",
                "children": [{
                    "key": "/kernel/KERNEL_NAMESPACE"
                }],
                'children_count': 1
            },
            [
                _DirectoriesMock(children=[
                    _Child(
                        "/kernel/KERNEL_NAMESPACE",  # noqa: E501;
                        "tfseks")
                ])
            ]),
        (
            {
                "type":
                "directory",
                "path":
                "/",
                "children": [{
                    "type":
                    "directory",
                    "path":
                    "/kernel",
                    "children": [{
                        "key": "/kernel/KERNEL_NAMESPACE"
                    }, {
                        "key": "/kernel/KERNEL_DOMAIN"
                    }],
                    "children_count":
                    2
                }],
                "children_count":
                1
            },
            [
                _DirectoriesMock(
                    children=[
                        _DirectoriesMock(
                            nodes=[
                                _Child(
                                    "/kernel/KERNEL_NAMESPACE",  # noqa: E501;
                                    "tfseks"),
                                _Child(
                                    "/kernel/KERNEL_DOMAIN",  # noqa: E501;
                                    "mcafee.soc")
                            ],
                            key="/kernel")
                    ],
                    key="/")
            ])
    ])
@mock.patch.dict('metamorphctl.commands.inventory.etcd.os.environ',
                 {'ETCDCTL_PEERS': 'http://localhost:2373'})
def test_collect_with_single_resource(etcd_inventory_output, read_side_effect):
    """Test when there are resources to collect from."""
    with mock.patch.object(Config, '__init__', lambda x: None), \
            mock.patch.object(Config, 'get') as mocked_config, \
            mock.patch('metamorphctl.commands.inventory.etcd.etcd', autospec=True) as etcd, \
            mock.patch('metamorphctl.commands.inventory.etcd.Etcd') as mock_etcd:

        mocked_config.return_value = {"etcd": ["key"]}

        mock_etcd.generate_output.return_value = etcd_inventory_output

        etcd.Client().read.side_effect = read_side_effect
        result = Etcd().collect()

        assert result == etcd_inventory_output
