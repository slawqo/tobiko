---

config:
  plugin_type: test
  entry_point: infrared.yaml


subparsers:

  tobiko:
    description: Deploy, configure and execute tobiko test cases
    include_groups: ["Ansible options", "Inventory", "Common options", "Answers file"]
    groups:

      - title: Topology options
        options:
          host:
            type: Value
            required: True
            default: localhost
            help: Target host where test cases are deployed and executed
            ansible_variable: test_host

      - title: Control flow
        options:
          stage:
            type: Value
            default: all
            ansible_variable: test_stage

      - title: Deploy stage
        options:
          clean-deploy-dir:
            type: Flag
            help: Cleanup directory where test cases will be downloaded
            ansible_variable: clean_deploy_dir
          tobiko-src-dir:
            type: Value
            help: Local directory where tobiko scripts are found
            ansible_variable: tobiko_src_dir
          tobiko-dir:
            type: Value
            help: Test host directory where Tobiko has to be deployed to
            ansible_variable: tobiko_dir
          tobiko-version:
            type: Value
            help: Git version to be used for checking out Tobiko scripts
            ansible_variable: tobiko_git_version
          tobiko-refspec:
            type: Value
            help: Git refspect to be used for checking out Tobiko scripts
            ansible_variable: tobiko_git_refspec

          test-src-dir:
            type: Value
            help: Local directory where test cases (and tox.ini file) are found
            ansible_variable: test_src_dir
          test-dir:
            type: Value
            help: Test host directory where test cases (and tox.ini file) are found
            ansible_variable: test_dir
          test-version:
            type: Value
            help: Git version to be used for checking out test scripts
            ansible_variable: test_git_version
          test-refspec:
            type: Value
            help: Git refspect to be used for checking out test scripts
            ansible_variable: test_git_refspec

      - title: Configure stage
        options:
          config:
            type: Value
            help: tobiko.conf file location
            ansible_variable: test_conf_file
          debug:
            type: Value
            help: enable/disable verbose log entries in tests results log file
            ansible_variable: test_log_debug

      - title: Run tox stage
        options:
          tox-dir:
            type: Value
            help: directory from where run tox (typically test_dir)
            ansible_variable: tox_dir
          tox-command:
            type: Value
            help: command to be executed for tox (typically tox)
            ansible_variable: tox_command
          tox-envlist:
            type: Value
            help: tox environment list to be executed
            ansible_variable: tox_envlist
          tox-extra-args:
            type: Value
            help: extra options to be passed to Tox
            ansible_variable: tox_extra_args
          test-report-dir:
            type: Value
            help: directory where to store test report files
            ansible_variable: test_report_dir
          test-report-name:
            type: Value
            help: prefix used to create report file names
            ansible_variable: test_report_name
          test-log-file:
            type: Value
            help: test cases log file
            ansible_variable: test_log_file

      - title: Collect stage
        options:
          collect-dir:
            type: Value
            help: local directory where report files are going to be copied to
            ansible_variable: test_collect_dir
