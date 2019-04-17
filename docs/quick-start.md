# Quick start guide

## Install Tobiko

virtualenv path/to/yuor/venv
source path/to/yuor/venv/bin/activate
pip install tobiko

## Set up credentials

In order to run the tests successfully you'll need to set up OpenStack credentials.
You can do it in one of two ways:

1. Using environment variables.
   Either by downloading the credentials file directly from your OpenStack project or
   setting them up manually like this:

       export API_VERSION = 2
       export OS_USERNAME = admin
       export OS_PASSWORD = admin
       export PROJECT_NAME = admin
       export OS_USER_DOMAIN_NAME="Default"
       export OS_PROJECT_DOMAIN_NAME = admin
       export OS_AUTH_URL=https://my_cloud:13000/v3


2. Setting up tobiko.conf file with the following format:

       api_version = 2
       username = admin
       password = admin
       project_name = admin
       user_domain_name = admin
       project_domain_name = admin
       auth_url = http://my_cloud:13000/v3

## Run Tests

To run neutron tests, use the following command:

    tox -e neutron
