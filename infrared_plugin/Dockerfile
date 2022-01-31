FROM fedora:34 as base

ENV TOBIKO_INFRARED_DIR /tobiko-infrared
ENV OPENSHIFT_INFRARED_URL=http://code.engineering.redhat.com/gerrit/openshift-ir-plugin.git
ENV WHEEL_DIR /wheel
ENV REPORT_DIR /report
ENV IR_HOME /infrared
ENV IR_EXTRA_ARGS ""

# Install common binary dependencies
RUN dnf install -y git python3 rsync which
RUN python3 -m ensurepip --upgrade
RUN python3 -m pip install --upgrade wheel setuptools

# Creates directories and use infrared home dir as home
RUN mkdir -p "${IR_HOME}" "${REPORT_DIR}"
WORKDIR "${IR_HOME}"


FROM base as install

# Install wheels
ADD requirements.txt .

RUN python3 -m pip install -r requirements.txt


FROM base as configure

# Copy python pacakges
COPY --from=install /usr/local /usr/local/

# Add optional plugins
RUN infrared plugin add "${OPENSHIFT_INFRARED_URL}" || true

# Add Tobiko plugin
ADD . "${TOBIKO_INFRARED_DIR}"
RUN infrared plugin add "${TOBIKO_INFRARED_DIR}"


FROM base as run

# Copy python pacakges
COPY --from=install /usr/local /usr/local/
# Copy infrared home dir
COPY --from=configure "${IR_HOME}" "${IR_HOME}"

# Create initial workspace
RUN infrared workspace checkout --create default

# Run Tobiko Infrared plugin
CMD infrared tobiko --collect-dir "${REPORT_DIR}" ${IR_EXTRA_ARGS}
