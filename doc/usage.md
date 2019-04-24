# Tobiko Usage Examples


## Faults

Use `tobiko-fault` to run only faults, without running resources population or tests.

Note: `tobiko-fault` can executed only from undercloud node.

To restart openvswitch service, run the following command:

    tobiko-fault --fault "restart openvswitch service"
