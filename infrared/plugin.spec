---
config:
    plugin_type: test

subparsers:
    tobiko:
        description: Tobiko Options
        include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
        groups:
            - title: Testing Parameters
              options:
                  tests:
                      type: Value
                      help: |
                          Group of tests to execute
