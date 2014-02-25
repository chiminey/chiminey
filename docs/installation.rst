Chiminey Installation Guide
===========================


This document describes how to install the chiminey system on a single VM, situated
in NeCTAR cloud, Vagrant or some other cloud solution.

Requirements
------------

Tested on VM with NeCTAR Centos 6.5 x86x64 Image and size m1.small, with 443/80/22 ports open


Instructions
------------

Install Chef-solo::

    sudo -s
    rpm  -Uvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    yum -y install ruby ruby-devel ruby-rdoc ruby-shadow gcc gcc-c++ automake autoconf make curl dmidecode
    cd /tmp
    curl -O http://production.cf.rubygems.org/rubygems/rubygems-1.8.10.tgz
    tar zxf rubygems-1.8.10.tgz
    cd rubygems-1.8.10
    ruby setup.rb --no-format-executable
    gem install chef --no-ri --no-rdoc


Get the chef script for the Chiminey app::

    yum -y install git
    mkdir -p /var/chef-solo
    cd /var/chef-solo
    git clone https://github.com/chiminey/chiminey-chef.git
    cd chiminey-chef
    if [[ $http_proxy != "" ]]; then echo http_proxy '"'$http_proxy'"' >> solo/solo.rb;  fi

Create a user for the Chiminey app::

    useradd bdphpc --create-home

Configure the user environment::

    su - bdphpc -c "ssh-keygen"   #return for all prompts
    su - bdphpc -c "mkdir ~/.python-eggs"
    su - bdphpc -c "touch /home/bdphpc/.ssh/known_hosts"

Install the Chiminey app::

    chef-solo -c solo/solo.rb -j solo/node.json -ldebug

Setup Chiminey app::

    su bdphpc
    cd /opt/chiminey/current/chiminey
    ../bin/django createsuperuser   # should only be used for admin tasks
    ../bin/django initial           # gets the database ready
    ../bin/django createuser        # a user who runs smart connectors


.. seealso::

        https://www.djangoproject.com/
           The Django Project

        https://docs.djangoproject.com/en/1.4/intro/install/
           Django Quick Install Guide


