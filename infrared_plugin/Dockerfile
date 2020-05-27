# Dockerfile that sets up InfraRed as documented here:
#  https://infrared.readthedocs.io/en/latest/bootstrap.html#setup

ARG base_image="docker.io/library/centos:8"

FROM "${base_image}" AS infrared

# Install required binary dependencies
RUN dnf install -y git \
                   libselinux-python3 \
                   python3 \
                   rsync \
                   which && \
    alternatives --set python /usr/bin/python3

# Get InfraRed sources with Git
ARG ir_src_dir=/src/infrared
ARG ir_git_url=https://github.com/redhat-openstack/infrared.git
ARG ir_git_refspec=master
ARG ir_git_remote=origin
RUN mkdir -p "${ir_src_dir}" && \
    cd "${ir_src_dir}" &&  \
    git init && \
    git remote add "${ir_git_remote}" "${ir_git_url}" && \
    git fetch "${ir_git_remote}" "${ir_git_refspec}" && \
    git checkout FETCH_HEAD
WORKDIR "${ir_src_dir}"
ENV IR_HOME=/opt/infrared

# Install InfraRed and its default plugins
# - First installs infrared requirements to workaround the too-may-files
#   problem related to temporary files removal final step
# - Then installs infrared itself
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade setuptools wheel && \
    (python3 -m pip install . || python3 -m pip install .) && \
    infrared plugin list && \
    (python3 -m pip cache purge || true)

# Creates persistent volume for IR workspaces
VOLUME ${IR_HOME}/.workspaces

# Sets default entry point
ENTRYPOINT ["infrared"]
CMD ["--help"]


# -----------------------------------------------------------------------------

FROM infrared as tobiko_plugin

# Add Tobiko plugin directory
ARG ir_tobiko_plugin=${ir_tobiko_plugin:-/src/infrared-tobiko}
RUN mkdir -p "${ir_tobiko_plugin}"
ADD . "${ir_tobiko_plugin}"

# Installs Tobiko plugin
RUN infrared plugin add "${ir_tobiko_plugin}"

# Sets tobiko as default command
CMD ["tobiko"]
