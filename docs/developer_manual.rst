
================
Developer Manual
================

.. _smart_connector_desc:
Smart Connector
---------------

A smart connector is composed of at least seven predefined core stages:
configure, create, bootstrap, schedule, execute, wait and destroy.
Depending of the expected functionality of a smart connector, one or
more of the core stages may need to be customised, and/or other stages
may need to be added. All core stages are located under
``chiminey/corestages``.

In general, creating a smart connector involves

-  customising existing and/or adding new stages as needed,
-  defining the smart connector based on these stages, and
-  registering the smart connector within Chiminey.


.. _payload:

Payload
~~~~~~~

A **payload** is a set of system and optionally domain-specific files that are needed for the correct
execution of a smart connector. The **system files** are composed of Makefiles and bash scripts
while the **domain-specific files** are developer provided executables.
The system files enable the Chiminey server to
setup the execution environment, execute domain-specific programs, and monitor the progress
of setup and execution.


**NB:** All smart connectors that are executed on  cloud and cluster infrastructure must have a payload.
However, smart connectors that are executed on unix servers do not need a payload unless the  execution is asynchronous.

Below is the structure of a payload; a payload template is available at  ``LOCAL_FILESYS_ROOT_PATH/payload_template``.



::

    payload_template/
        ├── bootstrap_done.sh
        ├── Makefile
        ├── process_payload
        │   ├── domain_specific
        │   │   ├── domain.sh
        │   │   └── ...
        │   ├── Makefile
        │   ├── process_running_done.sh
        │   ├── process_schedule_done.sh
        │   ├── start_process_schedule.sh
        │   └── start_running_process.sh
        ├── schedule_done.sh
        ├── start_bootstrap.sh
        └── start_schedule.sh


Examining the contents of a payload
"""""""""""""""""""""""""""""""""""

A payload contains two types of files: *domain-specific* and *system*. All domain-specific files are provided by the developer while
the system files are included in the Chiminey package. The system files are composed Makefiles and bash scripts.
The contents of some of the system files needs to be changed to satisfy the requirements of a specific smart connector.

    - The **Makefiles** provide API through which the Chiminey server sets-up execution environment, executes domain-specific programs and monitor setup and execution progress. Therefore, the contents of the Makesfiles must not be changed.

    - The **bash scripts** contain system and domain-specific information. The scripts that contain domain-specific blocks should be updated as needed.


Updating the domain-specific blocks of system files
"""""""""""""""""""""""""""""""""""""""""""""""""""

Here is the list of system files, in logical group and order:

    - :ref:`start_bootstrap.sh and bootstrap_done.sh <bootstrap_script>`
    - :ref:`start_schedule.sh and schedule_done.sh <schedule_script>`
    - :ref:`start_process_schedule.sh and process_schedule_done.sh <proc_schedule_script>`
    - :ref:`start_running_process.sh and process_running_done.sh <proc_running_script>`

.. _bootstrap_script:

start_bootstrap.sh, bootstrap_done.sh
'''''''''''''''''''''''''''''''''''''
These scripts are needed during the bootstrap stage for installing dependencies.

    - ``start_bootstrap.sh`` contains a list of instructions to install  dependencies.  For instance, if the new smart connector needs a fortran compiler and its execution environment is Centos,  then ``start_bootstrap.sh`` will have the following content:

      ::

        #!/bin/sh

        yum -y install gcc-gfortran

    - ``bootstrap_done.sh`` contains a list of instructions to confirm whether the installation of  dependencies is completed. When installation is completed, the script must write  ``Environment Setup Completed``. The Chiminey server assumes successful dependency installation when the server receives ``Environment Setup Completed``. Below is an example of checking the  completion of a fortran compiler installation.

      ::

        #!/bin/sh

        command -v f95 >/dev/null 2>&1 || { echo >&2 "f95 not installed Aborting."; exit 1; }
        echo Environment Setup Completed




.. _schedule_script:

start_schedule.sh, schedule_done.sh
'''''''''''''''''''''''''''''''''''
These files are needed during the schedule stage. Their content must not be changed.



.. _proc_schedule_script:

start_process_schedule.sh, start_running_process.sh
'''''''''''''''''''''''''''''''''''''''''''''''''''

These files are needed during the schedule stage for configuring/setting up the environment for individual process.
These scripts are useful especially when a smart connector has multiple processes, each with their own
configuration requirement.

    - ``start_process_schedule.sh``  contains the configuration instructions.

    - ``start_running_process.sh`` contains the instructions to  confirm whether the configuration is completed. When the configuration is completed, the script must write  ``Process Setup Completed``.


.. _proc_running_script:

start_running_process.sh, process_running_done.sh
'''''''''''''''''''''''''''''''''''''''''''''''''

These files are needed in the execute stage for running the domain-specific code, and in the wait stage for  monitoring the  progress of the execution.


    - ``start_running_process.sh`` contains the instructions for executing the domain-specific code. The output of the execution is expected to be redirected to ``chiminey/`` unless otherwise specified (see :ref:`smart connector configuration <>`). Suppose, the domain-specific executable  is a script, which is located at ``payload_name/process_payload/domain_specific/domain.sh``;    ``start_running_process.sh`` will have the following content:

      ::

        #!/bin/sh

        cd domain-specific; ./domain.sh > chiminey/output

    - ``process_running_done.sh`` contains the instructions for checking whether the execution is completed. Upon completion, the scripts must write ``stopped``. If the execution is synchronous, then the content should be

      ::

        #!/bin/bash
        echo stopped





      For asynchronous executions, process IDs can be used to  confirm completion. For this, the  ``start_running_process.sh`` should be  modified to capture the PID of the domain-specific execution.

      Here is the updated ``start_running_process.sh``:

      ::

        #!/bin/sh

        cd domain-specific; ./domain.sh > chiminey/output & echo $! > run.pid

      Here is the updated ``process_running_done.sh``, which uses PID to confirm completion:

      ::

        #!/bin/sh

        PID=`cat run.pid`
        if [ `ps -p $PID | wc -l` -gt 1 ]
        then
          # program is still running
          echo still running
        else
            echo stopped
..



..
    see hrmc payload
    All domain-specific files are provided by the developer.

     enable the Chiminey server to
    setup the execution environment, execute domain-specific code, and monitor the progress of setup and execution.
    The Chiminey server

     are the correct functionality of
    the Chiminey server

    describe domain-specific packages of work within a smart connector.
    It  provides a more sophisticated  assembly of software and their dependencies that the simple run commands of
    the previous example. These files are Makefiles, bash scripts, and optionally developer provided executables
    and other types of files. A template payload is provided under payload_template/.




    The Makefiles should not be changed. However, depending on dependency and the functionality of the the smart connector, one or more of the bash scripts need to be updated. All smart connectors should update the content of start_running_process.sh. This file holds the core functionality of a smart connector. Therefore,  in our example, we update the start_running_process.sh by appending



..
    .. _define_smart_connector:

    Defining a Smart Connector
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The process of defining a smart connector, in general, involves \*
    defining stages: which require specifying a name and the full package
    path to the stage's source code, and optionally setting constants that
    are needed during the execution of that stage; \* assembling predefined
    stages under a common parent stage; and \* attaching relevant UI form
    fields to the smart connector (for user input).

    Specifically, defining the random number smart connector involves,

    * :ref:`redefining the execute stage <redefine_exec_stage>`
    * :ref:`attaching UI form fields <attach_form_fields>`

    A smart connector can be registered within the Chiminey server in
    various ways. Here, a `Django management
    command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#management-commands-and-locales>`__
    is used.


    Parameter sweep is used to create multiple jobs, each with its set of
    parameter values (see `Parameter
    Sweep </chiminey/chiminey/wiki/Types-of-Input-Form-Fields#wiki-sweep>`__
    for details). This feature can be added to a smart connector by turning
    the sweep flag on during the `registration of the smart
    connector <#register_smart_conn>`__.


    1. :ref:`Quick Example: The Random Number Smart Connector for Non-Cloud Execution <quick_example>`


Examples
--------

Here, we use the following examples to show the different features of a smart connector
and how a smart connector is defined and registered within a Chiminey server.

.. toctree::
    quick_example
    randnumcloud

