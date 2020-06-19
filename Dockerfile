ARG base_image="docker.io/library/centos:8"

FROM "${base_image}" as base

# Make sure Git and Python 3 are installed on your system.
RUN yum install -y git python3 rsync which

# Check your Python 3 version is greater than 3.6
RUN python3 -c 'import sys; sys.version_info >= (3, 6)'

# Ensure Pip is installed and up-to date
RUN curl https://bootstrap.pypa.io/get-pip.py | python3

# Check installed Pip version
RUN python3 -m pip --version

# Ensure basic Python packages are installed and up-to-date
RUN python3 -m pip install --upgrade setuptools wheel virtualenv tox six

# Check installed Tox version
RUN tox --version


# -----------------------------------------------------------------------------

FROM base as sources

# Get Tobiko source code using Git
RUN mkdir -p /src
ADD . /src/tobiko
WORKDIR /src/tobiko


# -----------------------------------------------------------------------------

FROM sources as bindeps

# Ensure required binary packages are installed
RUN ./tools/install-bindeps.sh

# Check bindeps are installed
CMD tox -e bindeps


# -----------------------------------------------------------------------------

FROM bindeps as py3

# Prepare py3 Tox virtualenv
RUN tox -e py3 --notest

# Run unit yest cases
CMD tox -e py3


# -----------------------------------------------------------------------------

FROM py3 as venv

# Run bash inside py3 Tox environment
CMD tox -e venv


# -----------------------------------------------------------------------------

FROM py3 as functional

# Run functional test cases
CMD tox -e functional


# -----------------------------------------------------------------------------

FROM py3 as scenario

# Run scenario test cases
CMD tox -e scenario


# -----------------------------------------------------------------------------

FROM py3 as neutron

# Run scenario test cases
CMD tox -e neutron


# -----------------------------------------------------------------------------

FROM py3 as faults

# Run faults test cases
CMD tox -e faults


# -----------------------------------------------------------------------------

from bindeps as infrared

# Set Python 3 as default alternative for python command
RUN alternatives --set python /usr/bin/python3

# Prepare infrared Tox virtualenv
RUN tox -e infrared --notest

# Run Tobiko InfraRed plugin
CMD tox -e infrared
