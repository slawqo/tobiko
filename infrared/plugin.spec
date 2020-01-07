
---

config:
  plugin_type: test
  entry_point: ../roles/tobiko/main.yml

subparsers:
  tobiko:
    description: Configure and Run Tobiko Test Cases

    include_groups:
      - "Ansible options"
      - "Inventory"
      - "Common options"
      - "Answers file"

    groups:
      - title: Stages Control
        options:

          pre_run:
            type: Bool
            help: install and configure Tobiko test cases

          run_tests:
            type: Bool
            help: run verification test cases

          run_faults:
            type: Bool
            help: run disruptive operation test cases

          post_run:
            type: Bool
            help: fetch artifacts after test case execution

            - title: Install Options
              options:
                  tox_dir:
                      type: Value
                      default: "{{ ansible_env.HOME }}/tobiko"
                      help: |
                          The directory where Tobiko will be installed and used
                  overcloudrc:
                      type: Value
                      default: "{{ ansible_env.HOME }}/overcloudrc"
                      help: |
                          The path to the overcloudrc file
                  floating_network:
                      type: Value
                      default: "public"
                      help: |
                          Name of overcloud's floating_network
                  tests:
                      type: Value
                      help: |
                          The set of tests to execute
                      default: scenario
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
