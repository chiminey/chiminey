
.. _payload:

Payload
~~~~~~~

A **payload** is a set of system and optionally domain-specific files that are needed for the correct
execution of a smart connector. The **system files** are composed of Makefiles and bash scripts
while the **domain-specific files** are developer provided executables.
The system files enable the Chiminey server to
setup the execution environment, execute domain-specific programs, and monitor the progress
of setup and execution.


**NB:**
    - All smart connectors that are executed on  a cloud and a cluster infrastructure must have a payload. However, smart connectors that are executed on unix servers do not need a payload unless the  execution is asynchronous.

    - A payload template is available at  ``payload_template``, which should be used as the starting point to prepare a payload for any  smart connector. The main part of preparing a payload is  :ref:`including domain-specific contents <update_domain_specific_content>`  to  satisfy the requirements of a specific smart connector. The    naming convention of payloads is ``payload_unique_name``.

Below is the structure of a payload.

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
the system files are included in the Chiminey package. The system files are composed of Makefiles and bash scripts.
The content of some of the system files needs to be changed to satisfy the requirements of a specific smart connector.

    - The **Makefiles** provide API through which the Chiminey server sets-up execution environment, executes domain-specific programs and monitor setup and execution progress. Therefore, the contents of the Makesfiles must not be changed.

    - The **bash scripts** contain system and domain-specific information. The scripts that contain domain-specific blocks should be updated as needed.

.. _update_domain_specific_content:

Updating the domain-specific blocks of system files
"""""""""""""""""""""""""""""""""""""""""""""""""""

Here is the list of system files (only bash scripts),  in logical group and order:

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
These scripts are useful especially when a smart connector has multiple processes, each with its  own
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

    - ``process_running_done.sh`` contains the instructions for checking whether the execution is completed. Upon completion, the scripts must write ``stopped``.

      For  synchronous executions,  the content of ``process_running_done`` is

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


