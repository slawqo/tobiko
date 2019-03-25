---
config:
    plugin_type: test

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
                  env:
                      type: Value
                      help: |
                          The tox environment to use
                  dir:
                      type: Value
                      help: |
                          The directory where Tobiko will be installed and used
                  venv:
                      type: Value
                      default: '~/tobiko_venv'
                      help: |
                          path of existing virtual environment
