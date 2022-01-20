Install test cases within a virtualenv
--------------------------------------

The safest way to run test cases is to do it within a
`Virtualenv <https://virtualenv.pypa.io/en/latest/>`__. Here we are goint to see how
to setup an environment with all test case dependencies.

In **RHEL**, **CentOS** or **Fedora** install the following packages::

    sudo dnf install -y gcc git python3 python3-devel python3-pip which findutils

In **Debian** or **Ubuntu** install following packages::

    sudo apt update
    sudo apt install -y gcc git python3 python3-dev python3-pip

Ensure Pip is up-to-date::

    python3 -m pip install --upgrade --user pip

Ensure Tox is installed and up-to-date::

    python3 -m pip install --upgrade --user setuptools virtualenv wheel tox

Get source code using Git and enter into Tobiko source folder::

    git clone https://opendev.org/x/tobiko.git
    cd tobiko

Install remaining binary packages::

    tools/install-bindeps.sh

Crate the virtual environment with Tox::

    python3 -m tox -e py3 --notest

In case you want to activate the virtual environment you can then type::

    . .tox/py3/bin/activate

At this point the environment should have all dependencies installed for running test
cases.
