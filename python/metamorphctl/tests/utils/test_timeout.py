# -*- coding: utf-8 -*-
"""Test kubernetes utils."""

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

from time import sleep
from metamorphctl.utils.timeout import timeout, TimeOutException


def test_timeout_exceeded_raises_exception():
    """Test the exception is raised when the is exceeded."""
    try:
        raises_exception()
        raise RuntimeError("Should raise exception")
    except TimeOutException:
        print("OK")


def test_timeout_not_exceeded_not_raises_exception():
    """Test the exception is not raised when the is exceeded."""
    try:
        not_raises_exception()
    except TimeOutException:
        raise RuntimeError("Shouldn't be raised")


@timeout(1)
def raises_exception():
    """Raise exception dummy function."""
    sleep(2)


@timeout(2)
def not_raises_exception():
    """Not raise exception dummy function."""
    sleep(1)
