ARG base_image=python


FROM python:3.10 as python

ENV INSTALL_PACKAGES="apt install -y"
ENV CONSTRAINS_FILE=upper-constraints.txt

RUN apt update && apt install -y iperf3 iputils-ping ncat


FROM python:3.8 as lower-constraints

ENV INSTALL_PACKAGES="apt install -y"
ENV CONSTRAINS_FILE=lower-constraints.txt

RUN apt update && apt install -y iperf3 iputils-ping ncat


FROM fedora:35 as fedora

ENV CONSTRAINS_FILE=upper-constraints.txt
ENV INSTALL_PACKAGES="dnf install -y"

RUN ${INSTALL_PACKAGES} iperf3 gcc python3-devel


FROM ${base_image} as base

ENV TOBIKO_DIR=/tobiko
ENV WHEEL_DIR=/wheel

RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade setuptools wheel


FROM base as source

# Install binary dependencies
RUN ${INSTALL_PACKAGES} git

ADD .gitignore \
    extra-requirements.txt \
    requirements.txt \
    README.rst \
    setup.cfg \
    setup.py \
    test-requirements.txt \
    ${CONSTRAINS_FILE} \
    ${TOBIKO_DIR}/

ADD tobiko/ ${TOBIKO_DIR}/tobiko/
ADD .git ${TOBIKO_DIR}/.git/


FROM source as build

# Build wheel files
RUN python3 -m pip wheel -w ${WHEEL_DIR} \
    -c ${TOBIKO_DIR}/${CONSTRAINS_FILE} \
    -r ${TOBIKO_DIR}/requirements.txt \
    -r ${TOBIKO_DIR}/test-requirements.txt \
    -r ${TOBIKO_DIR}/extra-requirements.txt \
    --src ${TOBIKO_DIR}/


FROM base as install

# Install wheels
RUN mkdir -p ${WHEEL_DIR}
COPY --from=build ${WHEEL_DIR} ${WHEEL_DIR}
RUN python3 -m pip install ${WHEEL_DIR}/*.whl


FROM source as tobiko

# Run tests variables
ENV PYTHONWARNINGS=ignore::Warning
ENV OS_TEST_PATH=${TOBIKO_DIR}/tobiko/tests/unit
ENV TOX_REPORT_DIR=/report
ENV TOX_REPORT_NAME=tobiko_results
ENV TOBIKO_PREVENT_CREATE=false

# Write log files to report directory
RUN mkdir -p /etc/tobiko
RUN printf "[DEFAULT]\nlog_dir=${TOBIKO_REPORT_DIR}" > /etc/tobiko/tobiko.conf

# Copy tobiko tools
ADD tools/ ${TOBIKO_DIR}/tools/

# Copy python pacakges
COPY --from=install /usr/local /usr/local/

WORKDIR ${TOBIKO_DIR}
CMD tools/run_tests.py ${OS_TEST_PATH}


FROM tobiko as linters

ENV SKIP=check-executables-have-shebangs,pylint

# Copy configuration files
ADD .pre-commit-config.yaml \
    linters-requirements.txt \
    ${TOBIKO_DIR}/

RUN python3 -m pip install -r ${TOBIKO_DIR}/linters-requirements.txt
RUN pre-commit install --install-hooks

WORKDIR ${TOBIKO_DIR}
CMD pre-commit run -a
