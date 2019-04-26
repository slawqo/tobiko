.. _quick-start-guide:

=================
Quick Start guide
=================


Document Overview
-----------------

This document describes how to install execute Tobiko scenarios test cases
using Tox. To install Tobiko inside a virtualenv directory please refers to
:ref:`tobiko-install-guide`.


Install Required Packages
-------------------------

Make sure Gcc, Git and base Python packages are installed on your system.
For instance on RHEL Linux you could type::

    sudo yum install -y gcc git python python-devel

Make sure pip and setuptools are installed and up-to date::

    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    sudo pip install --upgrade setuptools

Make sure tox, virtualenv and wheel are installed and up to date::

    sudo pip install --upgrade tox virtualenv wheel


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

You can use an existing shell rc file that is valid for Python OpenStack
client::

    source openstackrc

An example of 'openstackrc' file could looks like below::

    export API_VERSION=2
    export OS_USERNAME=admin
    export OS_PASSWORD=secret
    export PROJECT_NAME=admin
    export OS_USER_DOMAIN_NAME=Default
    export OS_PROJECT_DOMAIN_NAME=admin
    export OS_AUTH_URL=https://my_cloud:13000/v3


.. _credentials-from-config:

Set Tobiko Credentials Via 'tobiko.conf' File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file at ~/.tobiko/tobiko.conf adding a section like below::

    [keystone]
    api_version = 2
    username = admin
    password = secret
    project_name = admin
    user_domain_name = admin
    project_domain_name = admin
    auth_url = http://my_cloud:13000/v3


Create Required Resources
~~~~~~~~~~~~~~~~~~~~~~~~~

Install Python OpenStack client::

    source overcloudrc
    sudo pip install python-openstackclient \
                     python-novaclient \
                     python-glanceclient

Create an image for Nova instances created by Tobiko::

    wget http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
    openstack image create "cirros" \
      --file cirros-0.3.5-x86_64-disk.img \
      --disk-format qcow2 \
      --container-format bare \
      --public

Create a flavor to be used with above image::

    openstack flavor create --id 0 --vcpus 1 --ram 64 --disk 1 m1.tiny

Add reference to above resources into your `tobiko.conf` file::

    [nova]
    image = cirros
    flavor = m1.tiny


Configure Public Network Name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add reference to the network where Tobiko should create floating IP instances::

    [neutron]
    floating_network = public


Run Test Cases
--------------

Run Tobiko scenario test cases using Tox::

    tox -e scenario
