# Quick start guide


## Before reading

This is work in progress and what documented here is still under development.
Some of below sections should be shorter here and more detailed in dedicated
documents. Because this documentation is a Draft for features still to be
implemented and discussed, its format and organization is secondary at this
stage and it is probably going to change soon.

## Overview

Tobiko is a tool used to prepare cloud test resources for system testing and
make them accessible to test cases written in Python with (or without) tempest.
The main purpose of Tobiko is taking out test resources management from test
cases to allow them to have a longer life than test case execution.

This a fundamental requirement that motivated this project with the purpose of
testing global cloud operations like whole cloud upgrades, reboot, migration.
It could also be used to test other smaller scale operations like for
example single node evacuation.

To avoid re-inventing the wheel Tobiko integrates some pre-existing tools
with the purpose of setting up and managing test resources. Example of such
tools integrated or to be integrated are:

 - OpenStack Python clients

 - OpenStack Heat Orchestration Service to manage test resources. The test
   developer is expected to use Heat as core tool for writing part of its test
   cases, in special cases test fixtures to reach initial test case state
   and to prepare test resources to be used inside test case. Tobiko should
   provide a Python interface to create Heat stacks starting from user provided
   "Heat Orchestartion Templates" and configuration parameters taken from
   user provided tobiko.conf file.

 - (TODO) Ansible Configuration Management tool user to prepare testing
   environment and test fixtures. Some fixtures are better handled by this
   non-Openstack generic tool, even if it offers a completly different approach
   to achieve the same purpose of Heat. Test developer should decide when to
   prefer this tool or others according his experience and his goals.

This is another peculiar aspect of Tobiko that distinguish it from other tools
like Tempest and it is being chosen mostly to take advantage of a good mature
production tool-set before introducing a new one from scratch.

It has been discussed about using tempest as fundamental toolset for setting
up resources and it has been forecast that to avoid some limitations and
complications Tempest has, it would be better to choose Orchestration
tools that has specifically designed for managing cloud resources from its
fundamentals. This has also another implicit minor advantage: Tobiko is also
a tool for testing Heat and regular OpenStack Python clients, while tempest
choose to re-implement clients and resources management from scratch (work
mostly incomplete and under very slow maintainance).


## Install Tobiko

Tobiko is preferably used from a dedicated virtual enviroment:

```
virtualenv path/to/virtualenv
source path/to/virtualenv/bin/activate
```

You can download Tobiko source code and install it in a single step inside
your environment by typing:

```
pip install git+https://git.openstack.org/openstack/tobiko
```

or simply

```
pip install tobiko
```

Tobiko doesn't need to be used from its source code directory, so, by instance,
after you installed it, you could use it as any Python tool from the directory
where your own test files are.

Tobiko is also distributed together with some example test cases that could
be used as a reference and this option grants you the ability to see if Tobiko
is properly installed on your system.


## Tobiko Workflow

Here we are going to describe the typical Tobiko workflow in a few simple
steps


### Step 1) Set up your cloud

Tobiko requires a pre-installed OpenStack cloud. As it relies on
python-openstackclient, you also have to assign environment variable with
the client credentials.

```
source <your-stackrc-file>
```

for example:

```
source overcloudrc
```

In order to verify Tobiko's connectivity, exectute following command:

```
openstack stack list
```

#### Configure Tobiko

Create your tobiko.conf file

TODO: document here minimal configuration file options required for executing
test cases.


### Step 2) Populate test resources

Tobiko creates a set of persisting resources (eventually using Heat) to be used
in test cases.

```
tobiko create
```

Tobiko is going to look into the current folder, searching into all registered
Python test packages for all test modules (Python files matching wildcard
expression ```test_*.py```). Every test case would eventually have a reference
to some Tobiko fixture. Some of these fixtures could be used as an example of a
stack of resources orchestracted from OpenStack Heat tool. By importing those
test case modules Tobiko will be able to find these fixtures and set them all
up.

The list of these fixtures can be narrowed down by using expressions to select
test cases to be considered. A test case could also be identified from its Python
source code files as below:

```
tobiko create [-f|--file] <test-case-files|test-case-dirs>...
```

Or it could be restricted using test case packages or file names as below:

```
tobiko create (-m|--module) <test-case-names|test-case-packages>...
```

To have a summary of all test cases which resouces could be set up using
Tobiko you could type:

```
tobiko list
```

To have a summary of all test cases which resouces has been actually set up
using Tobiko you can type:

```
tobiko list (-e|--existing)
```


### 3) Run test cases

Once test cloud resources (also called here Tobiko test fixtures) are ready to
be used, test cases can finally be executed to check if the cloud is working by
executing test cases with such preconfigured test resources.

To run test cases you can type:

```
tobiko run <test-case-files|test-case-dirs>...
```

or similarly to Tobiko create command:

```
tobiko run [-m|--module] <test-case-modules|test-case-packates>...
```

You can also use your favorite Python test runner as there are very good ones
around.

```
stestr ...
```

Please note Tobiko is only a wrapper around your favorite test runner and
you could change it by configuring Tobiko.

The first time that a test case requires test resources managed by Tobiko then
Tobiko is going to discover test case resources from your given stack name.
To achieve it, test case developer is expected to use Tobiko Python API.


### 4) Execute your cloud operation

In this step you should execute a sequence of cloud operations that you want to
test. For example you could upgrade your OpenStack installation in order to see
if the test resources managed by Tobiko are still working as expected.


### 5) Run test cases again

After executing your operations on top of your OpenStack instance, you should
expect test resources set up by Tobiko to still be there and they should pass
the same test cases that has been passed at step 3. So here you should execute
the same command line you executed at step 3:

```
tobiko run [<test-cases>]
```


### 6) Cleanup all populated resources

Finally once all your tests has been executed you can ask Tobiko to cleanup
all resources by typing below command:

```
tobiko delete
```

The previous command could also be more selective by deleting only test resources
for specific test cases:

```
tobiko delete <test-case-files|test-case-dirs>
```

```
tobiko delete (-m|--module) <test-case-modules|test-case-modules>
```
