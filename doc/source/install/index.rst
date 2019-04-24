============
Installation
============


Document Overview
-----------------

This document describes how to install Tobiko inside a Python virtualenv. For
a quick and simpler start you can jump to the Quick Start Guide.


Install Tobiko Using Virtualenv
-------------------------------

Make sure Gcc, Git and base Python packages are installed on your system.
For instance on RHEL Linux you could type::

    sudo yum install -y gcc git python python-devel

Make sure pip and setuptools are installed and up-to date::

    wget https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py
    sudo pip install --upgrade setuptools

Make sure tox, virtualenv and wheel are installed and up to date::

    sudo pip install --upgrade tox virtualenv wheel

Get Tobiko source code using Git::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko

To install Tobiko and its dependencies is safer to create a clean Virtualenv
where to install it. Create a Virtualenv and activate it::

    virtualenv .tobiko-env
    source .tobiko-env/bin/activate

Install Tobiko and its requirements::

    pip install \
        -c https://opendev.org/openstack/requirements/raw/branch/master/upper-constraints.txt \
        -r requirements.txt \
        -r extra-requirements.txt
    pip install .
