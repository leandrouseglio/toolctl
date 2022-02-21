# -*- coding: utf-8 -*-
"""Move images command."""

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

import re
import subprocess
import sys

import click
import boto3

from metamorphctl.utils.printutils import print_error, print_success


# pylint:disable=broad-except

@click.command()
@click.option("--registry", "-r", required=True, help="url of ECR registry")
@click.option(
    "--file",
    "-f",
    "images_file",
    default="images_to_move",
    help="file with images to be moved(defaults to ./images_to_move)",
)
def cli(registry, images_file):
    r"""Move images listed in a file to a ECR registry.

    REQUIREMENTS:\n
    - All listed images should be available on the local docker registry\n
    - Docker should be installed and with permissions to push to the registry\n
    - Aws credentials should be configured (available on ~/.aws/credentials)

    FILE FORMAT:\n
    Each line on the file should correspond to an image with the formats:

    [registry:port/]namespace/imagename:version OR

    imagename:version

    (where what is inside [] is optional)

    FILE EXAMPLE:\n
    artifactory-lvs.corpzone.internalzone.com:6565/metamorph/smart-container:v1.0.1\n
    metamorph/ubuntu:18.04-cis\n
    busybox:latest
    """
    print("Starting to move images")
    images = read_images_from_file(images_file)
    ecr = boto3.client("ecr")
    ecr_repositories = ecr.describe_repositories()["repositories"]

    # check that we are using the correct registry (just in case)
    id_from_argument = registry_id(registry)
    if not id_from_argument:
        print_error(f"Registry {registry} is not valid")
        sys.exit(1)
    # we assume that at least one ecr_repository exist
    id_from_ecr = registry_id(ecr_repositories[0]["repositoryUri"])
    if id_from_argument != id_from_ecr:
        error_msg = (
            f"id from registry URL ({id_from_argument}) does "
            f"not match id from ECR ({id_from_ecr})"
        )
        print_error(error_msg)
        sys.exit(1)

    for image in images:
        image_name, version = image_info(image)
        if not image_name:
            print_error(f"{image} is an invalid image name, skipping it")
            continue

        # checking repository
        try:
            result = ecr.create_repository(repositoryName=image_name)
            if not result:
                print_error(
                    f"Couldn't create {image_name} repository on ECR, skipping it"
                )
                continue
        except Exception as exception:
            # matching exception manually because i can't get it from boto3
            if exception.__class__.__name__ == "RepositoryAlreadyExistsException":
                pass
            print_error(
                f"Couldn't create {image_name} repository on ECR,"
                f"skipping it. Unknown error: {exception}"
            )
            continue

        # tag image
        newtag = f"{registry}/{image_name}:{version}"
        tag_image(image, newtag)

        # push image
        # pylint: disable=subprocess-run-check
        result = subprocess.run(
            ["docker", "push", newtag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if result.returncode > 0:
            print_error(f"There was a problem when pushing the image {newtag}")
            print_error(result.stdout.decode("UTF-8"))
            continue
        print_success(f"{image} pushed succesfully to {newtag}")


def image_info(image):
    """Extract image info from the string."""
    # this matches image names like:
    # regsitryurl.com:443/namespace/image:version
    # where the name of the image is "namespace/image"
    regex = re.compile(r"(?:.*\/)?(.*\/.*):(.*)$")
    match = regex.match(image)
    try:
        name = match.group(1)
        version = match.group(2)
    except (IndexError, AttributeError):
        # there were missing matches in the regex, or the match was None
        # try the other format
        #
        # this regex matches image names like:
        # image:version
        regex = re.compile(r"^([\w\.]*):([\w\.]*)$")
        match = regex.match(image)
        try:
            name = match.group(1)
            version = match.group(2)
        except (IndexError, AttributeError):
            return None, None
    return name, version


def registry_id(url):
    """Extract the ECR id from the registry url."""
    regex = re.compile(r"^(\d+)\..*\.ecr\..*$")
    match = regex.match(url)
    if not match:
        # the uri didn't match the regex, it probably is wrong
        # return None to notify the error
        return None
    return match.group(1)


def read_images_from_file(images_file):
    """Read the images and returns them as a list."""
    try:
        with open(images_file, "r") as img_file:
            images_raw = img_file.readlines()
            # remove newlines
            images = [image.strip() for image in images_raw]
    except FileNotFoundError:
        print_error(f"file {images_file} was not found")
        sys.exit(1)
    return images


def tag_image(oldtag, newtag):
    """Tags an image."""
    try:
        # pylint: disable=subprocess-run-check
        subprocess.run(["docker", "tag", oldtag, newtag])
    except FileNotFoundError:
        print_error("Docker was not found on PATH")
        sys.exit(1)
