.. _conf_logging:

Configure Logging
~~~~~~~~~~~~~~~~~

.. configure-tobiko-logging-label

Tobiko can configure a logging system to write messages to a log file. You can
edit the below options in :ref:`tobiko-conf` to enable it as below::

    [DEFAULT]
    # Whenever to allow debugging messages to be written out or not
    debug = true

    # Name of the file where log messages will be appended.
    log_file = tobiko.log

    # The base directory used for relative log_file paths.
    log_dir = .

The file 'tobiko.log' is the default file where test cases and the Python framework
are going to write their logging messages. By setting debug as 'True' you
ensure that messages with the lowest logging level are written there (DEBUG level).
The log_file location specified above is relative to the tobiko.conf file
location. In this example it is the Tobiko source files' directory itself.
