# Tobiko installation guide

## Install pip

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python get-pip.py

## Install Virtual Environment

sudo pip install virtualenv

## Install dependencies

sudo yum install gcc python-devel

## Clone Tobiko

git clone https://review.openstack.org/openstack/tobiko.git

## Create Virtual Environment

virtualenv ~/tobiko_venv && source ~/tobiko_venv/bin/activate

## Install Tobiko

cd tobiko
pip install -r extra-requirements.txt
pip install .