# -*- coding: utf-8 -*-
"""Move images command tests."""

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

from unittest.mock import patch, Mock
import tempfile

from click.testing import CliRunner

from metamorphctl.commands.move_images_command import cli
from metamorphctl.commands.move_images_command import image_info


TEST_REGISTRY_URI = "518861015603.dkr.ecr.us-west-2.amazonaws.com"
TEST_REGISTRY_ID = "518861015603"


@patch("builtins.open")
@patch("boto3.client")
@patch("subprocess.run")
def test_correct_move_images(subprocess_mock, boto3_mock, open_mock):
    """Test should move images when all is correct."""
    open_mock.return_value = _images_file()
    boto3_mock.return_value = _ecr_client()
    subprocess_mock.return_value = _subprocess_result()
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", TEST_REGISTRY_URI, "-f", "file_with_images"])

    assert res.exit_code == 0, res.output


@patch("builtins.open")
@patch("boto3.client")
@patch("subprocess.run")
def test_skip_when_fail_create_repository(subprocess_mock, boto3_mock, open_mock):
    """Tests that it continues when create a repository fails."""
    open_mock.return_value = _images_file()
    boto3_mock.return_value = _ecr_client_fail_on_create_repository()
    subprocess_mock.return_value = _subprocess_result()
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", TEST_REGISTRY_URI, "-f", "file_with_images"])

    assert res.exit_code == 0, res.output


@patch("builtins.open")
@patch("boto3.client")
@patch("subprocess.run")
def test_fail_when_not_docker_on_path(subprocess_mock, boto3_mock, open_mock):
    """Tests that the command fails when docker isn't installed."""
    open_mock.return_value = _images_file()
    boto3_mock.return_value = _ecr_client()
    subprocess_mock.return_value = _subprocess_no_docker()
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", TEST_REGISTRY_URI, "-f", "file_with_images"])

    assert res.exit_code > 0, res.output


@patch("builtins.open")
@patch("boto3.client")
@patch("subprocess.run")
def test_skip_when_push_image_fails(subprocess_mock, boto3_mock, open_mock):
    """Test that it doesn't fail when push image fails."""
    open_mock.return_value = _images_file()
    boto3_mock.return_value = _ecr_client()
    subprocess_mock.return_value = _subprocess_fail()
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", TEST_REGISTRY_URI, "-f", "file_with_images"])

    assert res.exit_code > 0, res.output


DIFFERENT_REGISTRY_URI = "999999999999.dkr.ecr.us-west-2.amazonaws.com"


def test_fail_when_different_registry_passed():
    """Test that fails when registries are different."""
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", DIFFERENT_REGISTRY_URI, "-f", "file_with_images"])
    assert res.exit_code > 0, res.output


WRONG_REGISTRY_URI = "ecr.us-west-2.amazonaws.com"


def test_fail_when_wrong_registry_passed():
    """Tests that fails when registry is invalid."""
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", WRONG_REGISTRY_URI, "-f", "file_with_images"])
    assert res.exit_code > 0, res.output


def test_fail_when_no_registry_passed():
    """Tests that fails when no registry is passed."""
    runner = CliRunner()
    res = runner.invoke(cli, ["-f", "file_with_images"])
    assert res.exit_code > 0, res.output


def test_image_info_with_bad_image():
    """Tests that returns None when image has invalid name."""
    bad_image = "bad+image+name"
    name, version = image_info(bad_image)
    assert name is None
    assert version is None


@patch("builtins.open")
@patch("boto3.client")
@patch("subprocess.run")
def test_skip_bad_image(subprocess_mock, boto3_mock, open_mock):
    """Tests that command continues when there is an invalid image."""
    open_mock.return_value = _bad_images_file()
    boto3_mock.return_value = _ecr_client()
    subprocess_mock.return_value = _subprocess_result()
    runner = CliRunner()
    res = runner.invoke(cli, ["-r", TEST_REGISTRY_URI, "-f", "file_with_images"])

    assert res.exit_code == 0, res.output


def _ecr_client():
    mock = Mock()
    mock.describe_repositories.return_value = _describe_repositories()
    mock.create_repository.return_value = _create_repository()
    return mock


def _ecr_client_fail_on_create_repository():
    # create ecr client to get RepositoryAlreadyExistsException
    # won't fail if there are no aws credentials
    mock = Mock()
    mock.describe_repositories.return_value = _describe_repositories()
    mock.create_repository.side_effect = Exception()
    return mock


def _describe_repositories():
    return {"repositories": [{"repositoryUri": TEST_REGISTRY_URI}]}


def _create_repository():
    return {
        "repository": {
            "registryId": TEST_REGISTRY_ID,
            "repositoryName": "metamorphctl/test",
        }
    }


def _subprocess_result():
    mock = Mock()
    mock.returncode = 0
    return mock


def _subprocess_fail():
    mock = Mock()
    mock.returncode = 1
    return mock


def _subprocess_no_docker():
    mock = Mock()
    mock.side_effect = FileNotFoundError("no docker")
    return mock


def _images_file():
    testfile = tempfile.TemporaryFile(mode="w+")
    testfile.write("metamorphctl/test:1.0.0\n")
    testfile.write(
        "artifactory-lvs.corpzone.internalzone.com:6565/metamorphctl/otherimage:v1.0.1\n"
    )
    testfile.write("busybox:latest\n")
    testfile.seek(0)
    return testfile


def _bad_images_file():
    testfile = tempfile.TemporaryFile(mode="w+")
    testfile.write("metamorphctl/test:1.0.0\n")
    testfile.write("bad+image+name\n")
    testfile.write("busybox:latest\n")
    testfile.seek(0)
    return testfile
