To execute commands from a virtualenv created by Tox, add the virtualenv name
to tox.ini envlist variable in the following way (in this example, the virtual
environment's name is 'venv')::

    [tox]

    envlist = other_environment_variables,venv

Run your commands as below::

    tox -e venv -- <your-commands>

For example::

    tox -e venv -- openstack network list
