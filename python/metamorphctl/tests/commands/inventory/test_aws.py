# -*- coding: utf-8 -*-
"""Aws unit tests."""

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
from metamorphctl.commands.inventory.aws import Aws
from metamorphctl.commands.inventory.aws_handlers.resource_tag import ResourceTag
from metamorphctl.utils.config import Config


def test_init_kernel_ns_not_present():
    """Test if init raise an exception when kernel_ns is not there."""

    with mock.patch("os.environ.get") as mocked_os:
        mocked_os.return_value = None
        with pytest.raises(ValueError):
            Aws()


def test_collect_no_requested_handlers():
    """Test that collect still works if there are no requested collector."""

    with mock.patch("os.environ.get") as mocked_os, \
            mock.patch.object(Config, "__init__", lambda x: None), \
            mock.patch.object(Config, "get") as mocked_config:
        mocked_os.return_value = "testns"
        mocked_config.return_value = {"aws": []}

        target = Aws()
        actual = target.collect()
        assert not actual  # tests this is an empty sequence


def test_collect_requested_handler_unavailable():
    """Test that collect still works if the requested handler is unavailable."""

    with mock.patch("os.environ.get") as mocked_os, \
            mock.patch.object(Config, "__init__", lambda x: None), \
            mock.patch.object(Config, "get") as mocked_config:
        mocked_os.return_value = "testns"
        mocked_config.return_value = {"aws": ["NonExistentHandler"]}

        target = Aws()
        actual = target.collect()
        assert not actual  # tests this is an empty sequence


def test_collect():
    """Test collect method."""
    # pytlint: disable=line-too-long
    with mock.patch("os.environ.get") as mocked_os, \
            mock.patch.object(Config, "__init__", lambda x: None), \
            mock.patch.object(Config, "get") as mocked_config, \
            mock.patch.object(ResourceTag, "__init__", lambda x, y: None), \
            mock.patch.object(ResourceTag, "handle") as mocked_handler:
        mocked_os.return_value = "testns"
        mocked_config.return_value = {"aws": ["ResourceTagMappingList"]}
        expected = "test"
        mocked_handler.return_value = {"Expected": expected}

        target = Aws()
        actual = target.collect()
        assert len(actual) == 1
        assert len(actual["ResourceTagMappingList"]) == 1
        assert actual["ResourceTagMappingList"]["Expected"] == expected


def test_collect_error_with_handler():
    """Test collect still works if there is an error with a handler."""
    # pytlint: disable=line-too-long
    with mock.patch("os.environ.get") as mocked_os, \
            mock.patch.object(Config, "__init__", lambda x: None), \
            mock.patch.object(Config, "get") as mocked_config, \
            mock.patch.object(ResourceTag, "__init__", lambda x, y: None), \
            mock.patch.object(ResourceTag, "handle") as mocked_handler:
        mocked_os.return_value = "testns"
        mocked_config.return_value = {"aws": ["ResourceTagMappingList"]}
        expected = "test"
        mocked_handler.side_effect = RuntimeError(expected)

        target = Aws()
        actual = target.collect()
        assert len(actual) == 1
        assert len(actual["ResourceTagMappingList"]) == 1
        assert actual["ResourceTagMappingList"]["error"] == expected
