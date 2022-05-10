#/!/bin/bash
#set -x

function wait_for_build_completion()
{
  running=`oc get pods --all-namespaces | grep build | grep Running | wc -l`
  while [ $running -ne 0 ]; do
    sleep 5
    running=`oc get pods --all-namespaces | grep build | grep Running | wc -l`
    echo "$running builds are still running"
  done
}

function wait_for_deployment_completion()
{
  running=`oc get pods --all-namespaces | grep deploy | grep Running | wc -l`
  while [ $running -ne 0 ]; do
    sleep 5
    running=`oc get pods --all-namespaces | grep deploy | grep Running | wc -l`
    echo "$running deployments are still running"
  done

}

function check_no_error_pods()
{
  error=`oc get pods --all-namespaces | grep Error | wc -l`
  if [ $error -ne 0 ]; then
    echo -e "Found pods in error state:\n$(oc get pods --all-namespaces | grep Error)"
    echo "details:"
    oc get pods --all-namespaces | grep Error | awk '{print "oc describe pod -n " $1" "$2}' | sh
    echo "$error pods in error state found, exiting"
    exit 1
  fi
}

wait_for_build_completion

wait_for_deployment_completion

check_no_error_pods
