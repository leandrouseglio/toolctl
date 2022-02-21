# -*- coding: utf-8 -*-
"""Holds tool configuration data."""

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

from os.path import expanduser, join
from ruamel import yaml


class Config():
    """Holds configs."""

    def __init__(self):
        """Init."""
        self.inner_config = {}
        try:
            # first, try to load the config
            # from user home folder
            folder = join(expanduser("~"), ".metamorphctl")
            self._load_from(folder)
        except IOError:
            # if it does not exist
            # try to load it from project folder
            # (this is useful at developing stage)
            self._load_from("metamorphctl")

    def get(self, key):
        """Return values."""
        return self.inner_config.get(key, None)

    def _load_from(self, folder):
        """Load a config file from given folder."""
        filename = join(folder, "config.yaml")
        with open(filename) as config_file:
            self.inner_config = yaml.safe_load(config_file)
        print("Configuration loaded from={}.".format(filename))
