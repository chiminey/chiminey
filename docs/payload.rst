
.. _payload:

Payload
~~~~~~~

A **payload** is a set of system and optionally domain-specific files that are needed for the correct
execution of a smart connector. The *system files* are composed of bash scripts
while the *domain-specific files* are developer provided executables.
The system files enable the Chiminey platform to
setup the execution environment, execute domain-specific programs, and monitor the progress
of setup and execution.


**NB:** All smart connectors that are executed on  a cloud and a cluster infrastructure must have a payload. However, smart connectors that are executed on unix servers do not need a payload unless the  execution is asynchronous.

..
    - A payload template is available at  ``payload_template``, which should be used as the starting point to prepare a payload for any  smart connector. The main part of preparing a payload is  :ref:`including domain-specific contents <update_domain_specific_content>`  to  satisfy the requirements of a specific smart connector. The    naming convention of payloads is ``payload_unique_name``.

Below is the structure of a payload.

::

    payload_name/
    |--- bootstrap.sh
    |--- process_payload
    │    |--- main.sh
    │    |--- schedule.sh
    │    |--- domain-specific executable





The names of the files and the directories under ``payload_name``, except the domain specific ones, cannot be changed.

  - ``bootstrap.sh`` includes instructions to install packages, which are needed by the smart connector job, on the compute resource.

  - ``schedule.sh`` is needed to add process-specific configurations. Some smart connectors spawn multiple processes to complete  a single job. If each process needs to be configured differently, the instruction on how to configure each process should be recorded in schedule.sh.

  - ``main.sh`` runs the core functionality of the smart connector, and writes the output to a file.

  - ``domain-specific executables`` are additional files that may be needed by main.sh.

Not all smart connector jobs require new packages to be installed, process-level configuration or additional domain-specific executables. On such cases, the minimal payload, as shown below, can be used.

::

    payload_name/
    |--- process_payload
    │    |--- main.sh


**NB:** Sample payloads are provided under each example smart connectors  at the `Chiminey Github Repository <https://github.com/chiminey/chiminey/tree/master/chiminey/examples>`_.
