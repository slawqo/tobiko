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
            help: Target host where test cases are deployed and executed
            ansible_variable: test_host

      - title: Control flow
        options:
          stage:
            type: Value
            ansible_variable: test_stage

      - title: Deploy stage
        options:
          clean:
            type: Flag
            help: Cleanup directory where test cases will be downloaded
            ansible_variable: clean_deploy_dir
          git-base:
            type: Value
            help: Git Url prefix where test projects are fetched from
            ansible_variable: git_base
          test-dir:
            type: Value
            help: Test host directory where test cases (and tox.ini file) are found
            ansible_variable: test_dir
          test-repo:
            type: Value
            help: Git URL from where to download test files
            ansible_variable: test_git_repo
          test-version:
            type: Value
            help: Git version to be used for checking out test scripts
            ansible_variable: test_git_version
          test-remote:
            type: Value
            help: Git remote name to be used for checking out test scripts
            ansible_variable: test_git_remote
          test-refspec:
            type: Value
            help: Git refspect to be used for checking out test scripts
            ansible_variable: test_git_refspec
          test-src-dir:
            type: Value
            help: Local directory where test cases (and tox.ini file) are found
            ansible_variable: test_src_dir
          tobiko-dir:
            type: Value
            help: Test host directory where Tobiko has to be deployed to
            ansible_variable: tobiko_dir
          tobiko-repo:
            type: Value
            help: Git URL from where to download tobiko files
            ansible_variable: tobiko_git_repo
          tobiko-version:
            type: Value
            help: Git version to be used for checking out Tobiko scripts
            ansible_variable: tobiko_git_version
          tobiko-remote:
            type: Value
            help: Git remote name to be used for checking out test scripts
            ansible_variable: tobiko_git_remote
          tobiko-refspec:
            type: Value
            help: Git refspect to be used for checking out Tobiko scripts
            ansible_variable: tobiko_git_refspec
          tobiko-src-dir:
            type: Value
            help: Local directory where tobiko scripts are found
            ansible_variable: tobiko_src_dir

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

      - title: Run stage
        options:
          workflow:
            type: Value
            help: name of workflow to execute
            ansible_variable: test_workflow
          tox-dir:
            type: Value
            help: directory from where run tox (typically test_dir)
            ansible_variable: tox_dir
          tox-command:
            type: Value
            help: command to be executed for tox (typically tox)
            ansible_variable: tox_command
          tox-environment:
            type: Value
            help: envitonment variables to be set when running test cases
            ansible_variable: tox_environment
          tox-envlist:
            type: Value
            help: Tox environment names to be executed
            ansible_variable: tox_envlist
          tox-extra-args:
            type: Value
            help: extra options to be passed to Tox
            ansible_variable: tox_extra_args
          tox-python:
            type: Value
            help: Python interpreter to be used for executing test cases
            ansible_variable: tox_python
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
            default: '{{ inventory_dir }}/{{ test_report_name }}'
