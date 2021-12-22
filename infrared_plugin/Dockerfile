FROM centos:8 as base

ENV TOBIKO_INFRARED_DIR /tobiko-infrared
ENV WHEEL_DIR /wheel
ENV REPORT_DIR /report
ENV IR_HOME /infrared
ENV IR_EXTRA_ARGS ""

# Install common binary dependencies
RUN dnf install -y git python3 rsync which
RUN python3 -m pip install --upgrade wheel setuptools pip


FROM base as source

# Populate tobiko-infrared source dir
ADD . ${TOBIKO_INFRARED_DIR}


FROM source as build

# Build Infrared wheel files
RUN python3 -m pip wheel -w ${WHEEL_DIR} -r ${TOBIKO_INFRARED_DIR}/requirements.txt


FROM base as install

# Install wheels
RUN mkdir -p ${WHEEL_DIR}
COPY --from=build ${WHEEL_DIR} ${WHEEL_DIR}
RUN pip install ${WHEEL_DIR}/*.whl


FROM source as tobiko-infrared

# Creates directories
RUN mkdir -p "${IR_HOME}" "${REPORT_DIR}"

# Copy python pacakges
COPY --from=install /usr/local /usr/local/

# Add tobiko plugin
RUN infrared plugin add "${TOBIKO_INFRARED_DIR}"

# Create initial workspace
RUN infrared workspace checkout --create default

# Use infrared home dir as home
WORKDIR ${IR_HOME}

# Run Tobiko Infrared plugin
CMD infrared tobiko --collect-dir "${REPORT_DIR}" ${IR_EXTRA_ARGS}
