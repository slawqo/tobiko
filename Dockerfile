ARG base_image=py39

FROM fedora:34 as py39

ENV CONSTRAINS_FILE=upper-constraints.txt
ENV INSTALL_PACKAGES="dnf install -y"
ENV INSTALL_PACKAGES_GROUP="dnf groupinstall -y"
ENV PYTHON_VERSION=3.9


FROM fedora:35 as py310

ENV CONSTRAINS_FILE=upper-constraints.txt
ENV INSTALL_PACKAGES="dnf install -y"
ENV INSTALL_PACKAGES_GROUP="dnf groupinstall -y"
ENV PYTHON_VERSION=3.10


FROM ${base_image} as base

ENV TOBIKO_DIR=/tobiko
ENV WHEEL_DIR=/wheel
ENV PYTHON=python${PYTHON_VERSION}

RUN ${INSTALL_PACKAGES} ${PYTHON}

RUN ${PYTHON} -m ensurepip --upgrade && \
    ${PYTHON} -m pip install --upgrade setuptools wheel pip


FROM base as source

# Install binary dependencies
RUN ${INSTALL_PACKAGES} git
RUN git config --global --add safe.directory "${TOBIKO_DIR}"

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

# Install development packages
RUN ${INSTALL_PACKAGES_GROUP} "Development Tools"
RUN ${INSTALL_PACKAGES} ${PYTHON}-devel

# Build wheel files
RUN mkdir -p ${WHEEL_DIR}
RUN ${PYTHON} -m pip wheel --wheel-dir ${WHEEL_DIR} \
    -c ${TOBIKO_DIR}/${CONSTRAINS_FILE} \
    -r ${TOBIKO_DIR}/requirements.txt \
    -r ${TOBIKO_DIR}/test-requirements.txt \
    -r ${TOBIKO_DIR}/extra-requirements.txt \
    --src ${TOBIKO_DIR}/


FROM base as install

# Install wheels
RUN mkdir -p ${WHEEL_DIR}
COPY --from=build ${WHEEL_DIR} ${WHEEL_DIR}
RUN ${PYTHON} -m pip install --prefix /usr/local ${WHEEL_DIR}/*.whl


FROM source as test

# Run tests variables
ENV PYTHONWARNINGS=ignore::Warning
ENV TOBIKO_REPORT_DIR=/report
ENV TOBIKO_REPORT_NAME=tobiko_results
ENV TOBIKO_PREVENT_CREATE=false
ENV TOBIKO_TEST_PATH=${TOBIKO_DIR}/tobiko/tests/unit

RUN ${INSTALL_PACKAGES} \
    findutils \
    iperf3 \
    iputils \
    nmap-ncat \
    procps \
    which

# Write log files to report directory
RUN mkdir -p /etc/tobiko
RUN printf "[DEFAULT]\nlog_dir=${TOBIKO_REPORT_DIR}" > /etc/tobiko/tobiko.conf

# Copy tobiko tools
ADD tools/ ${TOBIKO_DIR}/tools/

# Copy python pacakges
COPY --from=install /usr/local /usr/local/

WORKDIR ${TOBIKO_DIR}
CMD tools/run_tests.py ${TOBIKO_TEST_PATH}


FROM test as linters

ENV SKIP=check-executables-have-shebangs,pylint

# Copy configuration files
ADD .pre-commit-config.yaml \
    linters-requirements.txt \
    ${TOBIKO_DIR}/

# Copy python pacakges
COPY --from=install /usr/local /usr/local/

# Install linters tools
RUN ${PYTHON} -m pip install -r ${TOBIKO_DIR}/linters-requirements.txt
RUN pre-commit install --install-hooks

WORKDIR ${TOBIKO_DIR}
CMD pre-commit run -a
