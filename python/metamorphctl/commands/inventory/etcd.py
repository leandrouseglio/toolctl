# -*- coding: utf-8 -*-
"""ETCD collector."""

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
from urllib.parse import urlparse

import etcd

from metamorphctl.utils.config import Config

INVENTORY_NAME = "etcd"

DEFAULT_OUTPUT_VALUES = ["key", "value", "modifiedIndex", "createdIndex", "ttl", "expiration"]


class Etcd():
    """Class to handle ETCD."""

    def __init__(self):
        """Initialize ETCD class."""

        self.etcd_peers = os.environ.get("ETCDCTL_PEERS", None)
        if not self.etcd_peers:
            raise ValueError("ETCDCTL_PEERS env variable is not present.")
        tokenized_url = urlparse(str(self.etcd_peers))
        self.etcd_host, self.etcd_port = tokenized_url.netloc.split(":")
        self.protocol = tokenized_url.scheme

        self.etcd = etcd.Client(
            host=self.etcd_host,
            port=int(self.etcd_port),
            allow_reconnect=True,
            protocol=self.protocol)

        self.output_values = []
        desired_output = Config().get("inventory").get(INVENTORY_NAME)

        print("Available etcd keys={}, requested={}".format(DEFAULT_OUTPUT_VALUES, desired_output))
        if desired_output:
            for output in set(desired_output) & set(DEFAULT_OUTPUT_VALUES):
                self.output_values.append(output)
        else:
            raise ValueError("At least one etcd inventory value must be set in config.yaml!")

    def generate_output(self, etcd_values):
        """Generate output from etcd raw input."""

        def discover_nodes(subtree):
            """Obtain values recursively for each subtree."""
            output = {}
            if subtree.get("dir") and subtree.get("nodes"):  # Some directories are empty
                output["type"] = "directory"
                output["path"] = subtree["key"]
                if subtree.get("nodes"):
                    output["children"] = [discover_nodes(child) for child in subtree["nodes"]]
                    output["children_count"] = len(output["children"])
            else:
                for desired in self.output_values:
                    output[desired] = subtree.get(desired, "")
            return output

        etcd_dict = etcd_values.__dict__
        children = etcd_dict["_children"]
        output = {"type": "directory", "path": etcd_dict["key"], "children": []}
        for subdir in children:
            output["children"].append(discover_nodes(subdir))
            output["children_count"] = len(output["children"])
        return output

    def get_etcd_values(self, path="/"):
        """Obtain etdc values recursively."""
        etcd_values = self.etcd.read(path, recursive=True)
        return etcd_values

    def collect(self):
        """Collect data from ETCD."""
        etcd_values = self.get_etcd_values()
        return self.generate_output(etcd_values)
