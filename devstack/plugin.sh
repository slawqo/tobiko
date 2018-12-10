# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# source "${TOBIKO_PLUGIN_DIR}/customize_image.sh"


function tobiko_install {
  echo_summary "Installing tobiko-plugin"

  setup_dev_lib "tobiko"
}


function tobiko_test_config {
  local tobiko_conf=$(mktemp)
  if [ -f "${TOBIKO_CONF}" ]; then
    cp "${TOBIKO_CONF}" "${tobiko_conf}"
  fi

  # See ``lib/keystone`` where these users and tenants are set up
  echo_summary "Write identity options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" identity auth_url "$(get_auth_url)"
  iniset "${tobiko_conf}" identity username "${ADMIN_USERNAME:-admin}"
  iniset "${tobiko_conf}" identity password "${ADMIN_PASSWORD:-secret}"
  iniset "${tobiko_conf}" identity project "${ADMIN_TENANT_NAME:-admin}"
  iniset "${tobiko_conf}" identity domain "${ADMIN_DOMAIN_NAME:-Default}"

  echo_summary "Write compute options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" compute image_ref "$(get_image_ref)"
  iniset "${tobiko_conf}" compute flavor_ref "$(get_flavor_ref)"

  echo_summary "Write network options to ${TOBIKO_CONF}"
  iniset "${tobiko_conf}" network floating_network_name \
    "$(get_floating_network_name)"

  echo_summary "Apply changes to ${TOBIKO_CONF} file."
  sudo mkdir -p $(dirname "${TOBIKO_CONF}")
  sudo cp "${tobiko_conf}" "${TOBIKO_CONF}"
}


function get_auth_url {
  echo "${KEYSTONE_SERVICE_URI_V3:-${KEYSTONE_SERVICE_URI/v2.0/}}"
}

function get_image_ref {
  local image_ids=( $(openstack image list -f value -c ID \
                         --property status=active) )
  echo "${image_ids[0]}"
}


function get_flavor_ref {
  local flavor_ids=( $(openstack flavor list -f value -c ID \
                         --public) )
  echo "${flavor_ids[0]}"
}


function get_floating_network_name {
  local networks=( $(openstack network list -f value -c Name \
                      --enable --status ACTIVE \
                      --provider-network-type flat) )
  echo "${networks[0]}"
}


if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            tobiko_install
            ;;
        test-config)
            tobiko_test_config
            ;;
    esac
fi
