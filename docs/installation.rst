.. _installation_guide:

Chiminey Installation Guide
===========================


This document describes how to install a Chiminey platform via `Docker <https://www.docker.com>`_, which is an automatic software deployment tool.
# on a virtual machine.
#, situated in NeCTAR cloud, Vagrant or some other cloud solution.

Requirements
------------

Docker 1.7+ is needed. Follow the links below to install docker on your machine.

-  :ref:`mac_windows_req`

-  :ref:`linux_req`

.. _mac_windows_req:

Mac OS X and Windows
~~~~~~~~~~~~~~~~~~~~

Here, we create a virtual machine that runs docker.

1. Download Docker Toolbox from https://www.docker.com/toolbox.

2. When the download is complete, open the installation dialog box by double-clicking the downloaded file.

3. Follow the on-screen prompts to install the Docker toolbox. You may be prompted for password just before the installation begins. You need to enter your password to continue.

4. When the installation is completed, press ``Close`` to exit.

5. Verify that ``docker-engine`` and ``docker-compose`` are installed correctly.

  - Open Docker Quickstart Terminal from your application folder. The resulting output looks like the following:

  .. figure:: img/installation/dockerengine.png
      :align: center
      :alt:   Docker Terminal on Mac OS X or Windows
      :figclass: align-center

      Figure.  Docker Virtual Machine on Mac OS X or Windows

  - Run docker engine::

      docker run hello-world


    + `Expected output`. You will see a message similar to the one below.:

       Unable to find image ’hello-world:latest’ locally
       latest: Pulling from library/hello-world
       03f4658f8b78: Pull complete
       a3ed95caeb02: Pull complete
       Digest: sha256:8be990ef2aeb16dbcb92...
       Status: Downloaded newer image for hello-world:latest
       Hello from Docker.
       This message shows that your installation appears to be
           working correctly.
       ...

  - Run docker-compose::

      docker-compose --version

    + *Expected output*.
       a. If your OS is not an older Mac:

            docker-compose version x.x.x, build xxxxxxx
￼
       b. If your OS is an older Mac:

            Illegal instruction: 4

    This error can be fixed by upgrading docker-compose:

            pip install --upgrade docker-compose


.. _linux_req:

Linux
~~~~~~

Docker, specifically ``docker-engine`` and ``docker-compose``, needs to be installed directly on your linux-based OS. Refer to the Docker online documentaion to install the two packages:

1. `Docker-engine <https://docs.docker.com/engine/installation/>`_

2. `Docker-compose <https://docs.docker.com/compose/install/>`_


Installation Instructions
------------

1. Open

If you have MaC On the created VM::

    sudo -s
    rpm  -Uvh http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
    yum -y install ruby ruby-devel ruby-rdoc ruby-shadow gcc gcc-c++ automake autoconf make curl dmidecode
    cd /tmp
    curl -O http://production.cf.rubygems.org/rubygems/rubygems-1.8.10.tgz
    tar zxf rubygems-1.8.10.tgz
    cd rubygems-1.8.10

    # install ruby 1.9.3 as centos 6.5 has only 1.8 which is no good for chef
    # http://tecadmin.net/install-ruby-1-9-3-or-multiple-ruby-verson-on-centos-6-3-using-rvm/
    yum update
    yum install gcc-c++ patch readline readline-devel zlib zlib-devel
    yum install libyaml-devel libffi-devel openssl-devel make
    yum install bzip2 autoconf automake libtool bison iconv-devel
    yum remove libyaml-0.1.6
    cd /tmp
    curl -L get.rvm.io | bash -s stable
    source /etc/profile.d/rvm.sh
    rvm install 1.9.3

    #install chef
    ruby setup.rb --no-format-executable
    gem install chef --no-ri --no-rdoc -v 11.10.4


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

Check testcases::

    su bdphpc
    cd /opt/chiminey/current/
    bin/django test .

Setup Chiminey app::

    cd chiminey
    ../bin/django createsuperuser   # should only be used for admin tasks
    ../bin/django initial           # gets the database ready
    ../bin/django createuser        # a user who runs smart connectors


.. seealso::

        https://www.djangoproject.com/
           The Django Project

        https://docs.djangoproject.com/en/1.4/intro/install/
           Django Quick Install Guide
