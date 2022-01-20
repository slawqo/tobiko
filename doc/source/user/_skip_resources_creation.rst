Skipping resources creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. skipping-resources-creation-label

In some cases, for example when Tobiko is run after an upgrade of a cloud, it may be expected
that resources used for tests have already been created. Tobiko should not try to create
resources than and just run tests using what has already been created.
To configure Tobiko to not create test resources, the environment variable ``TOBIKO_PREVENT_CREATE``
can be used::

    export TOBIKO_PREVENT_CREATE=True

If this is set to ``True`` or ``1`` then Tobiko will not try to create resources like VMs,
networks, routers, or images and just run validations of what exists in the cloud already.
