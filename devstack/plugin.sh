# Directory where this plugin.sh file is
TOBIKO_PLUGIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# source "${TOBIKO_PLUGIN_DIR}/customize_image.sh"


function tobiko_install {
    setup_dev_lib "tobiko"
}


function tobiko_test_config {
    echo "TODO(fressi): generate tobiko.conf here"
}


if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            echo_summary "Installing tobiko-plugin"
            tobiko_install
            ;;
        test-config)
            echo_summary "Configuring tobiko options"
            tobiko_test_config
            ;;
    esac
fi
