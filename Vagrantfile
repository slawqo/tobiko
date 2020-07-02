# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Customize the count of CPU cores on the VM
CPUS = 4

# Customize the amount of memory on the VM
MEMORY = ENV.fetch("VM_SIZE", "4096").to_i

# Every Vagrant development environment requires a box. You can search for
# boxes at https://vagrantcloud.com/search.
BOX = ENV.fetch("VM_BOX", "generic/centos8")

# Machine host name
HOSTNAME = "tobiko"

# Top vagrantfile dir
VAGRANTFILE_DIR = File.dirname(__FILE__)

# Source provision playbook
PROVISION_PLAYBOOK = ENV.fetch(
  "PROVISION_PLAYBOOK", "#{VAGRANTFILE_DIR}/vagrant/devstack/provision.yaml")

# Host IP address to be assigned to OpenStack in DevStack
HOST_IP = "192.168.33.10"

# Red Hat supscription parameters
REDHAT_ACTIVATIONKEY = ENV.fetch("REDHAT_ACTIVATIONKEY", "")
REDHAT_USERNAME = ENV.fetch("REDHAT_USERNAME", "")
REDHAT_PASSWORD = ENV.fetch("REDHAT_PASSWORD", "")

# Local directory from where look for devstack project
DEVSTACK_SRC_DIR =  ENV.fetch(
  "DEVSTACK_SRC_DIR", "#{File.dirname(VAGRANTFILE_DIR)}/devstack")

# Local directory from where looking for tobiko project files
TOBIKO_SRC_DIR = ENV.fetch("TOBIKO_SRC_DIR", VAGRANTFILE_DIR)

# Local directory from where looking for requirements project files
REQUIREMENTS_SRC_DIR =  ENV.fetch(
  "REQUIREMENTS_SRC_DIR", "#{File.dirname(VAGRANTFILE_DIR)}/requirements")

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://vagrantcloud.com/search.
  config.vm.box = BOX
  # config.vm.box_version = "< 3.0"
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
  config.vm.network "private_network", ip: HOST_IP

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
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

  # Run provision playbook
  config.vm.provision "ansible" do |ansible|
    ansible.limit = 'all'
    ansible.playbook = PROVISION_PLAYBOOK
    ansible.extra_vars = ansible.extra_vars = {
      'redhat_activationkey' => REDHAT_ACTIVATIONKEY,
      'redhat_username' => REDHAT_USERNAME,
      'redhat_password' => REDHAT_PASSWORD,
      'devstack_src_dir' => DEVSTACK_SRC_DIR,
      'requirements_src_dir' => REQUIREMENTS_SRC_DIR,
      'tobiko_src_dir' => TOBIKO_SRC_DIR,
    }
  end

end
