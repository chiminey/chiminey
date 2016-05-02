.. _installation_guide:

Chiminey Installation Guide
===========================


This document describes how to install a Chiminey platform via `Docker <https://www.docker.com>`_, which is an automatic software deployment tool.


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


    + You will see a message similar to the one below::

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

    + The output will be ``docker-compose version x.x.x, build xxxxxxx``
    + For users with an older Mac, you will get ``Illegal instruction: 4``. This error can be fixed by upgrading docker-compose::

        pip install --upgrade docker-compose


.. _linux_req:

Linux
~~~~~~

Docker, specifically ``docker-engine`` and ``docker-compose``, needs to be installed directly on your linux-based OS. Refer to the Docker online documentation to install the two packages:

1. Install `docker-engine <https://docs.docker.com/engine/installation/>`_

2. Install `docker-compose <https://docs.docker.com/compose/install/>`_


Chiminey Installation
------------

1. For Mac OS X and Windows users, open `Docker Quickstart Terminal`. For linux-based OS users, login to your machine and open a terminal.

2. Check if ``git`` is installed. Type ``git`` on your terminal.

   + If git is installed, the following message will be shown::

       usage: git [--version] [--help] [-C <path>] ..
                  [--exec-path[=<path>]] [--html-path] [...
                  [-p|--paginate|--no-pager] [--no- ...
                  [--git-dir=<path>] [--work-tree=<path>]...
                  <command> [<args>]
                  ...

   + If git is not installed, you will see ``git: command not found``. Download and install ``git`` from http://git-scm.com/download


3. Clone the ``docker-chiminey`` source code from http://github.com.au::

     git clone https://github.com/chiminey/docker-chiminey.git


4. Change your working directory::

     cd docker-chiminey


5. Setup a self-signed certificate. You will be prompted to enter country code, state, city, and etc::

    sh makecert

6. Deploy the Chiminey platform::

    docker-compose up -d


7. Verify Chiminey was deployed successfully.

  - Retrieve IP address of your machine

      + For Mac and Windows users, type ``env | grep DOCKER_HOST``. The expected output has a format ``DOCKER_HOST=tcp://IP:port``, for example. ``DOCKER_HOST=tcp://192.168.99.100:2376``. Thus, your IP address is 192.168.99.100.

      + For linux users, the command ``ifconfig`` prints your our machine's IP address.

  - Open a browser and visit the Chiminey portal at IP, in our example, http://192.168.99.100. After a while, the Chiminey portal will be shown.

    .. figure:: img/installation/chimineyportal.png
        :align: center
        :alt:  Chiminey Portal
        :figclass: align-center

        Figure.  Chiminey Portal



.. seealso::

        https://www.djangoproject.com/
           The Django Project

        https://docs.djangoproject.com/en/1.4/intro/install/
           Django Quick Install Guide
