.. _tobiko-configuration-guide:

=============
Configuration
=============

This document describes how to configure Tobiko.

.. sidebar:: See also

    For a quick and simpler start you can jump to the
    :ref:`tobiko-quick-start-guide`.

    To install Tobiko inside a virutalenv please read
    :ref:`tobiko-installation-guide`.

    To run Tobiko scenario test cases please look at
    :ref:`tobiko-test-case-execution-guide`.


Configure Tobiko Framework
--------------------------

In order to make sure Tobiko tools can connect to OpenStack services via Rest
API configuration parameters can be passed either via environment variables or
via an INI configuration file (referred here as :ref:`tobiko-conf`). Please look
at :ref:`authentication-methods` for more details.


tobiko.conf
~~~~~~~~~~~

.. include:: _conf_explanation.rst
    :start-after: tobiko-conf-label

Configure Logging
~~~~~~~~~~~~~~~~~

.. include:: _conf_logging.rst
    :start-after: configure-tobiko-logging-label

.. include:: _conf_credentials.rst

.. _authentication-methods:

Authentication Methods
~~~~~~~~~~~~~~~~~~~~~~

Tobiko uses
`OpenStack client <https://docs.openstack.org/python-openstackclient/latest/>`__
to connect to OpenStack services.

Skipping resources creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: _skip_resources_creation.rst
    :start-after: skipping-resources-creation-label

What's Next
-----------

To know how to run Tobiko scenario test cases you can look at
:ref:`tobiko-test-case-execution-guide`
