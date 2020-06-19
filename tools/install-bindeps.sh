#!/bin/bash

set -ex

INSTALL_PACKAGE=$(which yum || which apt)

if ! tox -e bindep ; then
  .tox/bindep/bin/bindep -b | xargs -r "${INSTALL_PACKAGE}" install -y
  .tox/bindep/bin/bindep
fi
