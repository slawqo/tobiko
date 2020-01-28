#!/bin/bash

set -eux


if [ -r "./provisionrc" ]; then
  echo "Load parameters from RC file"
  source "./provisionrc" || true
fi

echo "Process script parameters and set default values when needed"
export PROVISION_DIR=${PROVISION_DIR:-$(cd "$(dirname "$0")" && pwd)}
export GIT_BASE=${OPENSTACK_GIT_BASE:-https://git.openstack.org}
export DEVSTACK_GIT_REPO=${DEVSTACK_GIT_REPO:-${GIT_BASE}/openstack-dev/devstack}
export DEVSTACK_GIT_BRANCH=${DEVSTACK_GIT_BRANCH:-stable/queens}
export DEST=${DEVSTACK_DEST_DIR:-/opt/stack}
export DEVSTACK_SRC_DIR=${DEVSTACK_SRC_DIR:-${DEST}/devstack}
export TOBIKO_SRC_DIR=${TOBIKO_SRC_DIR:-/vagrant}
export HOST_IP=${DEVSTACK_HOST_IP:-172.18.161.6}
export DEVSTACK_CONF_FILENAME=${DEVSTACK_CONF_FILENAME:-local.conf}

echo "Provisioning DevStack on host $(hostname) as user ${USER}"
echo "Current directory is $(pwd)"

echo "Make sure stack user has rigths to write to ${DEST} folder"
sudo chown -fR "${USER}.${USER}" "${DEST}"
sudo chmod ug+rwx "${DEST}"

if ! which git; then
  echo "Install Git"
  sudo yum install -y git
fi

if ! which python3; then
  echo "Install Git"
  # DevStack is not able to install Python3 on its own on CentOS 7
  sudo yum install -y python3
fi

if ! [ -d "${DEVSTACK_SRC_DIR}" ]; then

  echo "Download DevStack source files from ${DEVSTACK_GIT_REPO}#${DEVSTACK_GIT_BRANCH}"
  mkdir -p $(basename "${DEVSTACK_SRC_DIR}")
  git clone "${DEVSTACK_GIT_REPO}" -b "${DEVSTACK_GIT_BRANCH}" "${DEVSTACK_SRC_DIR}"
fi

echo "Configure DevStack"
cp "${PROVISION_DIR}/${DEVSTACK_CONF_FILENAME}" "${DEVSTACK_SRC_DIR}/local.conf"

cd "${DEVSTACK_SRC_DIR}"
echo "Run DevStack from directory: $(pwd)"

./stack.sh
