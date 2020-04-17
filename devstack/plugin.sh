# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)


function install_tobiko {
  echo_summary "Installing tobiko-plugin"

  if [ "${TOBIKO_BINDEP}" != "" ]; then
    install_python3
    install_bindep "${TOBIKO_DIR}/bindep.txt" test
  fi
}


function configure_tobiko {
  # Ensure any user can write to log file
  local log_dir=$(dirname ${TOBIKO_LOG_FILE})
  if ! [ -d "${log_dir}" ]; then
    sudo mkdir -p "${log_dir}"
  fi
  if ! [ -w "${TOBIKO_LOG_FILE}" ]; then
    sudo touch "${TOBIKO_LOG_FILE}"
    sudo chmod ugo+rw "${TOBIKO_LOG_FILE}"
  fi

  # Write configuration to a new temporary file
  local tobiko_conf_file=$(mktemp)
  if [ -f "${TOBIKO_CONF_FILE}" ]; then
    # Start from existing tobiko.conf file
    cp "${TOBIKO_CONF_FILE}" "${tobiko_conf_file}"
  fi

  configure_tobiko_default "${tobiko_conf_file}"
  configure_tobiko_cirros "${tobiko_conf_file}"
  configure_tobiko_glance "${tobiko_conf_file}"
  configure_tobiko_keystone "${tobiko_conf_file}"
  configure_tobiko_nova "${tobiko_conf_file}"
  configure_tobiko_neutron "${tobiko_conf_file}"

  echo_summary "Apply changes to actual ${TOBIKO_CONF_FILE} file."
  sudo mkdir -p $(dirname "${TOBIKO_CONF_FILE}")
  sudo mv "${tobiko_conf_file}" "${TOBIKO_CONF_FILE}"
  sudo chmod ugo+r "${TOBIKO_CONF_FILE}"

  echo "${TOBIKO_CONF_FILE} file content:"
  echo --------------------------------
  cat "${TOBIKO_CONF_FILE}"
  echo --------------------------------
}


function configure_tobiko_cirros {
  echo_summary "Write [cirros] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  iniset_nonempty "${tobiko_conf_file}" cirros name "${TOBIKO_CIRROS_IMAGE_NAME}"
  iniset_nonempty "${tobiko_conf_file}" cirros url "${TOBIKO_CIRROS_IMAGE_URL}"
  iniset_nonempty "${tobiko_conf_file}" cirros file "${TOBIKO_CIRROS_IMAGE_FILE}"
  iniset_nonempty "${tobiko_conf_file}" cirros username "${TOBIKO_CIRROS_USERNAME}"
  iniset_nonempty "${tobiko_conf_file}" cirros password "${TOBIKO_CIRROS_PASSWORD}"
}


function configure_tobiko_default {
  echo_summary "Write [DEFAULT] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  setup_logging "${tobiko_conf_file}"
  iniset ${tobiko_conf_file} DEFAULT debug "${TOBIKO_DEBUG}"
  iniset ${tobiko_conf_file} DEFAULT log_dir $(dirname "${TOBIKO_LOG_FILE}")
  iniset ${tobiko_conf_file} DEFAULT log_file $(basename "${TOBIKO_LOG_FILE}")
}


function configure_tobiko_glance {
  echo_summary "Write [glance] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  iniset_nonempty "${tobiko_conf_file}" glance image_dir "${TOBIKO_GLANCE_IMAGE_DIR}"
}


function configure_tobiko_keystone {
  echo_summary "Write [keystone] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  local api_version=${IDENTITY_API_VERSION}
  if [ "${api_version}" == '2' ]; then
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

  iniset "${tobiko_conf_file}" keystone cloud_name "${TOBIKO_KEYSTONE_CLOUD_NAME}"
  iniset "${tobiko_conf_file}" keystone api_version "${api_version}"
  iniset "${tobiko_conf_file}" keystone auth_url "${auth_url}"
  iniset "${tobiko_conf_file}" keystone username "${TOBIKO_KEYSTONE_USERNAME}"
  iniset "${tobiko_conf_file}" keystone password "${TOBIKO_KEYSTONE_PASSWORD}"
  iniset "${tobiko_conf_file}" keystone project_name "${TOBIKO_KEYSTONE_PROJECT_NAME}"

  if [ "${api_version}" != '2' ]; then
    iniset "${tobiko_conf_file}" keystone domain_name "${TOBIKO_KEYSTONE_DOMAIN_NAME}"
    iniset "${tobiko_conf_file}" keystone user_domain_name \
      "${TOBIKO_KEYSTONE_USER_DOMAIN_NAME}"
    iniset "${tobiko_conf_file}" keystone project_domain_name \
       "${TOBIKO_KEYSTONE_PROJECT_DOMAIN_NAME}"
    iniset "${tobiko_conf_file}" keystone trust_id "${TOBIKO_KEYSTONE_TRUST_ID}"
  fi
}


function configure_tobiko_nova {
  echo_summary "Write [nova] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  # Write key_file
  local key_file=${TOBIKO_NOVA_KEY_FILE:-}
  if [ "${key_file}" != "" ]; then
      iniset "${tobiko_conf_file}" nova key_file "${key_file}"
  fi
}


function configure_tobiko_neutron {
  echo_summary "Write [neutron] section to ${TOBIKO_CONF_FILE}"
  local tobiko_conf_file=$1

  # Write floating network
  local floating_network=${TOBIKO_NEUTRON_FLOATING_NETWORK}
  if [ "${floating_network}" != "" ]; then
    iniset "${tobiko_conf_file}" neutron floating_network "${floating_network}"
  fi
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
