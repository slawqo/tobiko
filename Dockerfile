ARG base_image="docker.io/library/centos:8"

FROM "${base_image}" as tobiko

# Install binary dependencies
RUN dnf install -y gcc git python3 python3-devel && \
    alternatives --set python /usr/bin/python3

# Get Tobiko source files
ARG tobiko_src_dir=.
ENV TOBIKO_DIR=/src/tobiko
# Copy Tobiko source files
RUN mkdir /src
ADD "${tobiko_src_dir}" "${TOBIKO_DIR}"
WORKDIR "${TOBIKO_DIR}"

# Install Python requirements
ARG constraints_file=https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt
ENV PIP_INSTALL="python -m pip install -c ${constraints_file}"
RUN set -x && \
    python --version && \
    ${PIP_INSTALL} --upgrade pip && \
    ${PIP_INSTALL} --upgrade setuptools wheel && \
    ${PIP_INSTALL} -r ./requirements.txt && \
    ${PIP_INSTALL} ./


# -----------------------------------------------------------------------------

FROM tobiko as tests

RUN ${PIP_INSTALL} -r ./test-requirements.txt

# Run test cases
ENV OS_LOG_CAPTURE=true
ENV OS_STDOUT_CAPTURE=true
ENV OS_STDERR_CAPTURE=true
ENV OS_TEST_PATH=tobiko/tests/unit
ENTRYPOINT ./tools/run_tests.py
