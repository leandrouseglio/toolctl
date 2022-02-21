# -*- coding: utf-8 -*-
"""Timeout decorator that raises an exception when the time has come."""

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

import signal


class TimeOutException(Exception):
    """Raised when a timeout happens."""


def timeout(timeout_secs):
    """Timeout decorator.

    Raise a TimeOutException exception after timeout seconds
    if the decorated function did not return.
    """

    def decorate(func):
        # pylint: disable=unused-argument
        def handler(signum, frame):
            raise TimeOutException()

        def new_f(*args, **kwargs):

            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout_secs)

            result = func(*args, **kwargs)  # func() always returns, in this scheme

            signal.signal(signal.SIGALRM, old_handler)  # Old signal handler is restored
            signal.alarm(0)  # Alarm removed

            return result

        return new_f

    return decorate
