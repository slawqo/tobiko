.. _tobiko-setup-workstation:

=================================
How to setup a tobiko workstation
=================================

*This guide should help contributors to configure their workstation, so it would be easier for them to write tobiko*
*test cases.*

Configuring local test running and debugging
--------------------------------------------

Clone the tobiko repository::

    git clone https://opendev.org/x/tobiko.git

Create a tobiko.conf inside the tobiko directory, which will have::

    [DEFAULT]

    debug = true

Inside the Tobiko directory, run::

    tox -e py3

Copy the path you see in the first line (it should contain something similar to *tobiko/.tox/py3*)

On Pycharm:
 * Create a new (pycharm) project with *Location = <the tobiko path>*

 * In interpreter options tab, choose “*New environment using Virtualenv*”, with Location = *<tobiko-path>/.pycharm*, and then click on "*Create -> Create from Existing Sources*".

 * Enter preferences (ctrl+alt+s in Linux)

 * In Project Interpreter tab:
    * Click * -> Add
    * Choose "*Existing Environment*"
    * In the Interpreter field, paste the path you copied after running the tox command, and add the "/bin/python3" suffix.

      Example: the path *~/tobiko/.tox/py3/bin/python3* might be used, as tox provides the directory *~/tobiko/.tox/py3*, and we add */bin/python3*

    * In Python Integrated Tools tab, under *Testing* section, set the *Default test runner* to be "*pytest*"

Now verify your environment has the configuration options mentioned above by doing the following:
Find tobiko/tests/unit/test_config.py in the left project window -> right click -> *Run pytest in test config*.

All tests should pass. You could also debug tests by setting a breakpoint.

Configuring proxy jump
----------------------

Make sure you can ssh to your remote host without a password:

.. include:: ../user/_conf_credentials.rst
    :start-after: define-your-ssh-variables:

And that’s it!
