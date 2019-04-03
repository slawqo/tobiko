# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)


function install_tobiko {
  echo_summary "Installing tobiko-plugin"
  install_python3
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
  configure_keystone_credentials

  echo_summary "Write compute service options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" nova image "$(get_image)"
  iniset "${tobiko_conf}" nova flavor "$(get_flavor)"

  echo_summary "Write networking options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" neutron floating_network \
    "$(get_floating_network)"

  echo_summary "Apply changes to ${TOBIKO_CONF} file."
  sudo mkdir -p $(dirname "${TOBIKO_CONF}")
  sudo cp "${tobiko_conf}" "${TOBIKO_CONF}"
  sudo chmod ugo+r "${TOBIKO_CONF}"
}


function get_keystone_auth_url {
  echo "${KEYSTONE_AUTH_URI_V3:-${KEYSTONE_AUTH_URI/v2.0}}"
}


function get_image {
  local name=${DEFAULT_IMAGE_NAME:-}
  if [ "${name}" != "" ]; then
    openstack image show -f value -c id "${name}"
  else
    openstack image list --limit 1 -f value -c ID --public --status active
  fi
}


function configure_keystone_credentials {
  echo_summary "Write Keystone service options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" keystone auth_url "$(get_keystone_auth_url)"

  TOBIKO_PROJECT_ID=$(get_or_create_project \
    "${TOBIKO_KEYSTONE_PROJECT_NAME}" "${TOBIKO_KEYSTONE_PROJECT_DOMAIN_NAME}")

  TOBIKO_USER_ID=$(get_or_create_user ${TOBIKO_KEYSTONE_USERNAME} \
    "${TOBIKO_KEYSTONE_PASSWORD}" "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}")

  get_or_add_user_project_role "${TOBIKO_KEYSTONE_USER_ROLE}" \
    "${TOBIKO_USER_ID}" "${TOBIKO_PROJECT_ID}"

  get_or_add_user_domain_role "${TOBIKO_KEYSTONE_USER_ROLE}" \
    "${TOBIKO_USER_ID}" "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}"

  iniset "${tobiko_conf}" keystone username "${TOBIKO_KEYSTONE_USERNAME}"
  iniset "${tobiko_conf}" keystone password "${TOBIKO_KEYSTONE_PASSWORD}"
  iniset "${tobiko_conf}" keystone project_name "${TOBIKO_KEYSTONE_PROJECT_NAME}"
  iniset "${tobiko_conf}" keystone user_domain_name \
    "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}"
  iniset "${tobiko_conf}" keystone project_domain_name \
    "${TOBIKO_KEYSTONE_PROJECT_DOMAIN_NAME}"
}

function get_flavor {
  local name=${DEFAULT_INSTANCE_TYPE:-}
  if [ "${name}" != "" ]; then
    openstack flavor show -f value -c id "${name}"
  else
    openstack flavor list --limit 1 -f value -c ID --public
  fi
}


function get_floating_network {
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
