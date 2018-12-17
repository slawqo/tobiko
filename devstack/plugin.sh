# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)


function install_tobiko {
  echo_summary "Installing tobiko-plugin"
  apt_get install python3-dev
  setup_dev_lib tobiko
}


function configure_tobiko {
  # Write configuration to a new temporary file
  local tobiko_conf=$(mktemp)
  if [ -f "${TOBIKO_CONF}" ]; then
    # Start from existing tobiko.conf file
    cp "${TOBIKO_CONF}" "${tobiko_conf}"
  fi

  # See ``lib/keystone`` where these users and tenants are set up
  echo_summary "Write identity service options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" identity auth_url "$(get_auth_url)"
  iniset "${tobiko_conf}" identity username "${ADMIN_USERNAME:-admin}"
  iniset "${tobiko_conf}" identity password "${ADMIN_PASSWORD:-secret}"
  iniset "${tobiko_conf}" identity project "${ADMIN_TENANT_NAME:-admin}"
  iniset "${tobiko_conf}" identity domain "${ADMIN_DOMAIN_NAME:-Default}"

  echo_summary "Write compute service options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" compute image_ref "$(get_image_ref)"
  iniset "${tobiko_conf}" compute flavor_ref "$(get_flavor_ref)"

  echo_summary "Write networking options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" network floating_network_name \
    "$(get_floating_network_name)"

  echo_summary "Apply changes to ${TOBIKO_CONF} file."
  sudo mkdir -p $(dirname "${TOBIKO_CONF}")
  sudo cp "${tobiko_conf}" "${TOBIKO_CONF}"
  sudo chmod ugo+r "${TOBIKO_CONF}"
}


function get_auth_url {
  echo "${KEYSTONE_SERVICE_URI_V3:-${KEYSTONE_SERVICE_URI/v2.0/}}"
}


function get_image_ref {
  local name=${DEFAULT_IMAGE_NAME:-}
  if [ "${name}" != "" ]; then
    openstack image show -f value -c id "${name}"
  else
    openstack image list --limit 1 -f value -c ID --public --status active
  fi
}


function get_flavor_ref {
  local name=${DEFAULT_INSTANCE_TYPE:-}
  if [ "${name}" != "" ]; then
    openstack flavor show -f value -c id "${name}"
  else
    openstack flavor list --limit 1 -f value -c ID --public
  fi
}


function get_floating_network_name {
  # the public network (for floating ip access) is only available
  # if the extension is enabled.
  # If NEUTRON_CREATE_INITIAL_NETWORKS is not true, there is no network created
  # and the public_network_id should not be set.
  local name=${PUBLIC_NETWORK_NAME:-}
  if [ "${name}" != "" ]; then
    openstack network show -f value -c name "${name}"
  else
    local networks=( $( openstack network list -f value -c Name --enable \
                                               --external) )
    echo "${networks[0]}"
  fi
}


if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            install_tobiko
            ;;
        test-config)
            configure_tobiko
            ;;
    esac
fi
