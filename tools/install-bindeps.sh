#!/bin/bash

set -ex

INSTALL_PACKAGE=$(which yum || which apt)
SUDO=$(which sudo || true)

if ! tox -e bindep ; then
  .tox/bindep/bin/bindep -b | xargs -r ${SUDO} "${INSTALL_PACKAGE}" install -y
  .tox/bindep/bin/bindep
fi
