.. _tobiko-installation-guide:

=========================
Tobiko Installation Guide
=========================


Document Overview
-----------------

This document describes how to install Tobiko inside a
`Python Virtualenv <https://virtualenv.pypa.io/en/latest/>`__.

.. sidebar:: See also

    For a quick and simpler start you can jump to the
    :ref:`tobiko-quick-start-guide`.

    To configure Tobiko please read :ref:`tobiko-configuration-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.

Install Tobiko Using Virtualenv
-------------------------------

Make sure Gcc, Git and base Python packages are installed on your system.

For instance on RHEL Linux 7.6 or CentOS 7 you could type::

    sudo yum install -y gcc git python python-devel wget

For instance on RHEL Linux 8 or CentOS 8 you could type::

    sudo dnf install -y gcc git python3 python3-devel wget
    sudo alternatives --set python /usr/bin/python3

Make sure pip is installed and up-to date::

    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    PIP=$(which pip)

Make sure setuptools, virtualenv and wheel are installed and up to date::

    sudo $PIP install --upgrade setuptools virtualenv wheel

Get Tobiko source code using Git and enter into Tobiko source folder::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko

To install Tobiko and its dependencies is safer to create a clean Virtualenv
where to install it. Create a Virtualenv and activate it::

    virtualenv .tobiko-env
    source .tobiko-env/bin/activate

Install Tobiko and its requirements::

    pip install \
        -c https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt \
        .


What's Next
-----------

To know how to configure Tobiko please read :ref:`tobiko-configuration-guide`.
