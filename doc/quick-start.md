# Quick start guide

## Install Tobiko
sudo yum install python-virtualenv
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


## Quick Start Setup&Run Template:
```bash
sudo yum install python-virtualenv.noarch -y
virtualenv ~/tobiko_venv && source ~/tobiko_venv/bin/activate
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install tox
sudo yum install gcc python-devel -y
git clone https://opendev.org/x/tobiko.git
cd tobiko
pip install -r extra-requirements.txt; pip install .

. ~/overcloudrc
wget http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img
openstack image create "cirros" \
  --file cirros-0.3.5-x86_64-disk.img \
  --disk-format qcow2 --container-format bare \
  --public
openstack flavor create --id 0 --vcpus 1 --ram 64 --disk 1 m1.tiny

cat > tobiko.conf <<EOF
[neutron]
floating_network='public'
[nova]
image='cirros'
flavor = 'm1.tiny'
EOF

tox -e neutron |& tee tox_neutron.out

```