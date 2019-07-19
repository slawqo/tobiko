# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)


function install_tobiko {
  echo_summary "Installing tobiko-plugin"
  install_python3
  setup_dev_lib tobiko
}


function configure_tobiko {
  # Write configuration to a new temporary file
  local tobiko_config=$(mktemp)
  if [ -f "${TOBIKO_CONFIG}" ]; then
    # Start from existing tobiko.conf file
    cp "${TOBIKO_CONFIG}" "${tobiko_config}"
  fi

  configure_tobiko_default "${tobiko_config}"
  configure_tobiko_cirros "${tobiko_config}"
  configure_tobiko_glance "${tobiko_config}"
  configure_tobiko_keystone "${tobiko_config}"
  configure_tobiko_nova "${tobiko_config}"
  configure_tobiko_neutron "${tobiko_config}"

  echo_summary "Apply changes to actual ${TOBIKO_CONFIG} file."
  sudo mkdir -p $(dirname "${TOBIKO_CONFIG}")
  sudo mv "${tobiko_config}" "${TOBIKO_CONFIG}"
  sudo chmod ugo+r "${TOBIKO_CONFIG}"

  echo "${TOBIKO_CONFIG} file content:"
  echo --------------------------------
  cat "${TOBIKO_CONFIG}"
  echo --------------------------------
}


function configure_tobiko_cirros {
  echo_summary "Write [cirros] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  iniset_nonempty "${tobiko_config}" cirros name "${TOBIKO_CIRROS_IMAGE_NAME}"
  iniset_nonempty "${tobiko_config}" cirros url "${TOBIKO_CIRROS_IMAGE_URL}"
  iniset_nonempty "${tobiko_config}" cirros file "${TOBIKO_CIRROS_IMAGE_FILE}"
  iniset_nonempty "${tobiko_config}" cirros username "${TOBIKO_CIRROS_USERNAME}"
  iniset_nonempty "${tobiko_config}" cirros password "${TOBIKO_CIRROS_PASSWORD}"
}


function configure_tobiko_default {
  echo_summary "Write [DEFAULT] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  setup_logging "${tobiko_config}"
  iniset ${tobiko_config} DEFAULT log_dir "${TOBIKO_LOG_DIR}"
  iniset ${tobiko_config} DEFAULT log_file "${TOBIKO_LOG_FILE}"
  iniset ${tobiko_config} DEFAULT debug "${TOBIKO_DEBUG}"
}


function configure_tobiko_glance {
  echo_summary "Write [glance] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  iniset_nonempty "${tobiko_config}" glance image_dir "${TOBIKO_GLANCE_IMAGE_DIR}"
}


function configure_tobiko_keystone {
  echo_summary "Write [keystone] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  local api_version=${IDENTITY_API_VERSION}
  if [ "${api_version}" == '2']; then
    local auth_url=${KEYSTONE_AUTH_URI/v2.0}
  else
    local auth_url=${KEYSTONE_AUTH_URI_V3:-${KEYSTONE_AUTH_URI/v3}}
  fi

  local project_id=$(get_or_create_project \
    "${TOBIKO_KEYSTONE_PROJECT_NAME}" \
    "${TOBIKO_KEYSTONE_PROJECT_DOMAIN_NAME}")

  local user_id=$(get_or_create_user \
    "${TOBIKO_KEYSTONE_USERNAME}" \
    "${TOBIKO_KEYSTONE_PASSWORD}" \
    "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}")

  local user_project_role_id=$(get_or_add_user_project_role \
    "${TOBIKO_KEYSTONE_USER_ROLE}" \
    "${user_id}" \
    "${project_id}")

  local user_domain_role_id=$(get_or_add_user_domain_role \
    "${TOBIKO_KEYSTONE_USER_ROLE}" \
    "${user_id}" \
    "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}")

  iniset "${tobiko_config}" keystone api_version "${api_version}"
  iniset "${tobiko_config}" keystone auth_url "${auth_url}"
  iniset "${tobiko_config}" keystone username "${TOBIKO_KEYSTONE_USERNAME}"
  iniset "${tobiko_config}" keystone password "${TOBIKO_KEYSTONE_PASSWORD}"
  iniset "${tobiko_config}" keystone project_name "${TOBIKO_KEYSTONE_PROJECT_NAME}"

  if [ "${api_version}" != '2' ]; then
    iniset "${tobiko_config}" keystone domain_name "${TOBIKO_KEYSTONE_DOMAIN_NAME}"
    iniset "${tobiko_config}" keystone user_domain_name \
      "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}"
    iniset "${tobiko_config}" keystone project_domain_name \
       "${TOBIKO_KEYSTONE_PROJECT_DOMAIN_NAME}"
    iniset "${tobiko_config}" keystone trust_id "${TOBIKO_KEYSTONE_TRUST_ID}"
  fi
}


function configure_tobiko_nova {
  echo_summary "Write [nova] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  # Write key_file
  local key_file=${TOBIKO_NOVA_KEY_FILE:-}
  iniset "${tobiko_config}" nova key_file "${key_file}"
}


function configure_tobiko_neutron {
  echo_summary "Write [neutron] section to ${TOBIKO_CONFIG}"
  local tobiko_config=$1

  # Write floating network
  local floating_network=${TOBIKO_NEUTRON_FLOATING_NETWORK}
  if [ "${floating_network}" != "" ]; then
    local floating_network=$(openstack network show -f value -c name "${floating_network}")
  else
    local networks=( $( openstack network list -f value -c Name --enable --external) )
    local floating_network=${networks[0]}
  fi
  iniset "${tobiko_config}" neutron floating_network "${floating_network}"
}


function iniset_nonempty {
  # Calls iniset only when option value is not an empty string
  if [ -n "$4" ]; then
    iniset "$@"
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
