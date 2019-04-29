.. _tobiko-quick-start-guide:

========================
Tobiko Quick Start Guide
========================


Document Overview
-----------------

This document describes how to install execute Tobiko scenarios test cases
using `Tox <https://tox.readthedocs.io/en/latest/>`__.

.. sidebar:: See also

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


Install Required Packages
-------------------------

Make sure Gcc, Git and base Python packages are installed on your system.

For instance on RHEL Linux you could type::

    sudo yum install -y gcc git python python-devel

For instance on RHEL Linux 8 or CentOS 8 you could type::

    sudo dnf install -y gcc git python3 python3-devel wget
    sudo alternatives --set python /usr/bin/python3

Make sure pip and setuptools are installed and up-to date::

    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    PIP=$(which pip)

Make sure setuptools, wheel, virtualenv, and tox are installed and up to date::

    sudo $PIP install --upgrade setuptools wheel virtualenv tox


Get Tobiko
----------

Get Tobiko source code using Git::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko


Configure Tobiko Credentials
----------------------------

In order to run the tests successfully you'll need to set up OpenStack
credentials. You can do it in one of below ways:

- :ref:`credentials-from-env`
- :ref:`credentials-from-config`


.. _credentials-from-env:

Set Tobiko Credentials Via Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: See also

    For more details about supported environment variables please read
    :ref:`authentication-environment-variables` section.

You can use an existing shell RC file that is valid for
`Python OpenStack client <https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html#environment-variables>`__
::

    source openstackrc

An example of 'openstackrc' file could looks like below::

    export OS_IDENTITY_API_VERSION=3
    export OS_AUTH_URL=https://my_cloud:13000/v3
    export OS_USERNAME=admin
    export OS_PASSWORD=secret
    export OS_PROJECT_NAME=admin
    export OS_USER_DOMAIN_NAME=Default
    export OS_PROJECT_DOMAIN_NAME=Default


.. _credentials-from-config:

Set Tobiko Credentials Via :ref:`tobiko-conf` File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sidebar:: See also

    For more details about supported configuration options please read
    :ref:`authentication-configuration` section.

Create a file at `~/.tobiko/tobiko.conf` adding a section like below::

    [keystone]
    api_version = 3
    auth_url = http://my_cloud:13000/v3
    username = admin
    password = secret
    project_name = admin
    user_domain_name = Default
    project_domain_name = Default


Setup Required Resources
~~~~~~~~~~~~~~~~~~~~~~~~

To be able to execute Tobiko scenario test cases there some OpenStack
resources that has to be created before running test cases.

To execute commands from a virtualenv created by Tox you can type as below::

    tox -e venv -- <your-commands>

You need to make sure ref:`authentication-environment-variables` are properly
set::

    tox -e venv -- openstack image list
    tox -e venv -- openstack flavor list
    tox -e venv -- openstack network list

`Get an image <https://docs.openstack.org/image-guide/obtain-images.html>`__
for Nova instances created by Tobiko::

    wget -c http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img
    tox -e venv -- openstack image create cirros \
      --file cirros-0.4.0-x86_64-disk.img \
      --disk-format qcow2 \
      --container-format bare \
      --public

Create a flavor to be used with above image::

    tox -e venv -- openstack flavor create --vcpus 1 --ram 64 --disk 1 m1.tiny

Create an SSH key file to be used to ssh to Nova server instances::

    ssh-keygen -f ~/.ssh/id_rsa -P ''

Add reference to above resources into your :ref:`tobiko-conf` file::

    [nova]
    image = cirros
    flavor = m1.tiny
    key_file=~/.ssh/id_rsa

Add reference to the network where Tobiko should create floating IP instances
in :ref:`tobiko-conf` file::

    [neutron]
    floating_network = public


Run Test Cases
--------------

Finally run Tobiko scenario test cases using Tox::

    tox -e scenario

List resources stacks created by test cases::

    tox -e venv -- openstack stack list
