"""Setup the package creation and installation."""
import os
from setuptools import setup, find_packages, Command


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""

    user_options = []

    def initialize_options(self):  # noqa
        pass

    def finalize_options(self):  # noqa
        pass

    def run(self):  # noqa
        os.system('rm -vrf ./build ./dist '  # nosec
                  './*.pyc ./*.tgz ./*.egg-info')


__version__ = "0.0.2"

setup(
    name="metamorphctl",
    version=__version__,
    author="McAfee Investigator Fernet Team",
    author_email="copperfield-all@mcafee.onmicrosoft.com",
    description=("service with handy commands to interact with metamorph and friends"),
    long_description=("metamorphctl "
                      "Python module with handy commands to interact with metamorph"
                      " and friends for troubleshooting purposes"),
    keywords='metamorphctl metamorph fernet',
    license="McAfee Confidential",
    url="https://github-lvs.corpzone.internalzone.com/mcafee/metamorphctl",
    packages=find_packages(exclude=['docs', 'tests']),
    entry_points={'console_scripts': ['metamorphctl = metamorphctl.cli:cli']},
    install_requires=[
        "ruamel.yaml==0.16.10",
        "regex==2020.05.14",
        "kubernetes==11.0.0",
        "boto3==1.13.19",
        "python-etcd==0.4.5",
        "click==7.1.2",
        "Jinja2==2.11.2",
        "jsonschema==3.2.0",
        "jmespath==0.10.0",
        "xlsxwriter==1.2.8"
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'License :: McAfee Confidential'
    ],
    include_package_data=True)
