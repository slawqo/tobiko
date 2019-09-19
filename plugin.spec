---
config:
    plugin_type: test
    entry_point: ./infrared/main.yml

subparsers:
    tobiko:
        description: Executes Tobiko Framework
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Stages Control
              options:
                  install:
                      type: Bool
                      help: |
                          Install Tobiko
            - title: Install Options
              options:
                  dir:
                      type: Value
                      default: "{{ ansible_env.HOME }}/tobiko"
                      help: |
                          The directory where Tobiko will be installed and used
                  overcloudrc:
                      type: Value
                      default: "{{ ansible_env.HOME }}/overcloudrc"
                      help: |
                          The path to the overcloudrc file
                  venv:
                      type: Value
                      default: "{{ ansible_env.HOME }}/tobiko_venv"
                      help: |
                          path of existing virtual environment
                  floating_network:
                      type: Value
                      default: "public"
                      help: |
                          Name of overcloud's floating_network
                  tests:
                      type: Value
                      help: |
                          The set of tests to execute
                      default: neutron
                  results_dir_suffix:
                      type: Value
                      help: |
                          Suffix string to add to tobiko_results dir
                          example : default will be tobiko_results_1st
                      default: "1st"
                  refsec:
                      type: Value
                      help: |
                          specific gerrit patch refsec to
                          checkout, example:
                          --refsec refs/changes/66/665966/7
                      default: ''
