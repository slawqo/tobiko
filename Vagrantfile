# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Customize the count of CPU cores on the VM
CPUS = 2

# Customize the amount of memory on the VM
MEMORY = 12288

# Every Vagrant development environment requires a box. You can search for
# boxes at https://vagrantcloud.com/search.
BOX = "generic/ubuntu1804"

HOSTNAME = "tobiko"

# Directory where Vagrantfile directory is copied or mounted to the VM
TOBIKO_SRC_DIR = "/vagrant"

# Default prefix to OpenStack Git repositories
OPENSTACK_GIT_BASE = "https://git.openstack.org"

# DevStack Git repo URL and branch
DEVSTACK_GIT_REPO = "#{OPENSTACK_GIT_BASE}/openstack-dev/devstack"
DEVSTACK_GIT_BRANCH = "master"

# DevStack destination directory
DEVSTACK_DEST_DIR = "/opt/stack"

# DevStack source file directory
DEVSTACK_SRC_DIR = "#{DEVSTACK_DEST_DIR}/devstack"

# Host IP address to be assigned to OpenStack in DevStack
DEVSTACK_HOST_IP = "172.18.161.6"



# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  config.vm.box = BOX
  config.vm.hostname = HOSTNAME

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # NOTE: This will enable public access to the opened port
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine and only allow access
  # via 127.0.0.1 to disable public access
  # config.vm.network "forwarded_port", guest: 80, host: 8080, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network "private_network", ip: DEVSTACK_HOST_IP

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network", ip: "172.18.161.6"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:

  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

    vb.cpus = CPUS
    vb.memory = MEMORY
  end

  config.vm.provider "libvirt" do |libvirt|
    libvirt.cpus = CPUS
    libvirt.memory =  MEMORY
  end

  config.vm.synced_folder ".", "/vagrant", type: "rsync",
    rsync__exclude: ".tox/"

  # View the documentation for the provider you are using for more
  # information on available options.

  # Use the same DNS server as the host machine
  config.vm.provision "file", source: "/etc/resolv.conf",
    destination: "~/resolv.conf"
  config.vm.provision "shell", privileged: false,
    inline: "sudo mv ~/resolv.conf /etc/resolv.conf"

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    set -uex
    if ! sudo su - stack; then
      # setup stack user
      sudo useradd -s /bin/bash -d '#{DEVSTACK_DEST_DIR}' -m stack
      echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
    fi

    if ! [ -d '#{DEVSTACK_DEST_DIR}/tobiko' ]; then
      sudo mkdir -p '#{DEVSTACK_DEST_DIR}/tobiko'
      sudo mount --bind /vagrant '#{DEVSTACK_DEST_DIR}/tobiko'
    fi

    # Generate provision RC file to pass variables to provision script
    sudo echo '
      export TOBIKO_SRC_DIR=#{TOBIKO_SRC_DIR}
      export OPENSTACK_GIT_BASE=#{OPENSTACK_GIT_BASE}
      export DEVSTACK_GIT_REPO=#{DEVSTACK_GIT_REPO}
      export DEVSTACK_GIT_BRANCH=#{DEVSTACK_GIT_BRANCH}
      export DEVSTACK_SRC_DIR=#{DEVSTACK_SRC_DIR}
      export DEVSTACK_DEST_DIR=#{DEVSTACK_DEST_DIR}
      export DEVSTACK_HOST_IP=#{DEVSTACK_HOST_IP}
    ' > ./provisionrc
    sudo mv ./provisionrc '#{DEVSTACK_DEST_DIR}/provisionrc'

    # Execute provision script as stack user
    sudo su -l stack -c '#{TOBIKO_SRC_DIR}/devstack/vagrant/provision.bash'
  SHELL
end
