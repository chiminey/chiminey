
================
Developer Manual
================



.. _chiminey:

Chiminey
--------

Main topics

- :ref:`Smart Connector <smart_connector_desc>`

- :ref:`Smart connector job submission UI <smart_connector_ui>`

- :ref:`Payload <payload>`


- :ref:`Examples <examples>`


.. _smart_connector_desc:

Smart Connector
~~~~~~~~~~~~~~~

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




.. _smart_connector_ui:

Smart Connector Job Submission UI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Chiminey server  automatically generates a job submission web page for each smart connector.
However, this web page contains only a drop down menu of :ref:`presets <manage_presets>`. The web page
will also
contain a `parameter sweep <https://github.com/chiminey/chiminey/wiki/Types-of-Input-Form-Fields#sweep>`__
input field for smart connectors with a sweep feature.
Since these two input fields are not sufficient to submit a job,
the developer should specify the input fields that are needed to submit
a particular smart connector job.
This is done during the :ref:`definition of the smart connector <constrtuct_smart_conn_ui>`.


There are various `input field types <https://github.com/chiminey/chiminey/wiki/Types-of-Input-Form-Fields>`_ like
computation platform, location and domain-specific variables.
Some of the fields are already included within the Chiminey platform. But others, especially the domain-specific
ones, will be defined by the developer.
The following table shows the list of input field types and their corresponding schema namespaces included within the Chiminey platform.

**NB**: The default value of ``NAMESPACE_PREFIX`` is ``"http://rmit.edu.au/schemas"``


+-----------------------------------------------------------+-----------------------------------------------------------+
|                    Schema Namespace                       |            Input Field Type                               |
+===========================================================+===========================================================+
| ``NAMESPACE_PREFIX+"/input/system/compplatform"``         |   A dropdown menu containing **all** registered
|                                                           |   computation platform names
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/system/compplatform/unix"``    | A dropdown menu containing only **unix** and
|                                                           | **cluster** computation platform names
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/system/compplatform/cloud"``   | A dropdown menu containing only **cloud**
|                                                           | computation platform names
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/system/cloud"``                | Two textfields for entering  the maximum and
|                                                             minimum **number of virtual machines**
|                                                           | needed for the job.
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/location"``                    | Two textfields for entering  **input** and **output**
|                                                           | locations (unix storage platform names)
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/location/output"``             | A textfield for entering  as  **output** location
|                                                           | (a unix storage platform)
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/location/input"``              | A textfield for entering   **input** location
|                                                           | (a unix storage platform)
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/reliability"``                 | A set of fields to control the degree of the
|                                                           | provided fault tolerance support
+-----------------------------------------------------------+-----------------------------------------------------------+
| ``NAMESPACE_PREFIX+"/input/mytardis"``                    | A dropdown menu containing all registered
|                                                             MyTardis deployments, a checkbox to turn
|                                                             on data curation, and  a textfield to
|                                                           | specify MyTardis experiment number
+-----------------------------------------------------------+-----------------------------------------------------------+


===========  ================
1. Hallo     | blah blah blah
               blah blah blah
               blah
             | blah blah
2. Here      We can wrap the
             text in source
32. There    **aha**
===========  ================



.. _constrtuct_smart_conn_ui:

Constructing Smart Connector Input Fields
"""""""""""""""""""""""""""""""""""""""""

Here, we see how to include the input fields that are needed for submitting a smart connector job.
The required job submission input fields must be specified when a :ref:`smart connector is defined <smart_connector_desc>`.
This is done via ``get_ui_schema_namespace(self)`` of the ``CoreInitial`` class.
The ``CoreInitial`` class is available at ``chiminey/initialisation/coreinitial``.

Suppose the new smart connector is cloud-based and writes its output to a unix server.
Therefore, the job submission page of this smart connector must include two input fields to enter
a cloud-based computation platform  and a unix-based output location. This is done by overwriting
``get_ui_schema_namespace(self)`` to include the following:

- ``NAMESPACE_PREFIX+"/input/system/compplatform/cloud"``

- ``NAMESPACE_PREFIX+"/input/location/output"``.

Here is the full content of ``get_ui_schema_namespace(self)``:

::

    def get_ui_schema_namespace(self):
        NAMESPACE_PREFIX = "http://rmit.edu.au/schemas"
        schema_namespaces = [
                NAMESPACE_PREFIX + "/input/system/compplatform/cloud",
                NAMESPACE_PREFIX + "/input/location/output",
                ]
        return schema_namespaces


.. _domain_specific_input_fields:

Including domain-specific input fields
''''''''''''''''''''''''''''''''''''''

Input field types that are included within the Chiminey platform are generic, and therefore domain-specific input
fields must be defined when needed. New input field types are defined in  ``get_domain_specific_schemas(self)``
of the  ``CoreInitial`` class. The definition includes

- **schema namespace** like ``NAMESPACE_PREFIX+"/input/domain_specific"``

- **descrption** of the type like *Domain-specific input field type*

- list of **input fields**: Each input field has

    - **type**:  There are three types of input fields: *numeric* (models.ParameterName.NUMERIC), *string* (models.ParameterName.STRING), *list of strings* (models.ParameterName.STRLIST). *numeric* and *string* inputs have a text field while a *list of strings* has a drop-down menu. Enduser inputs are validated against the type of the input field.

    - **subtype**: Subtypes are used for additional validations: *numeric* fields can validated for containing  whole and natural numbers.

    - **description**: The label of the input field.

    - **choices**: If the type is *list of strings*, the values of the dropdown menu is provided via *choices*.

    - **ranking**: Ranking sets the ordering of input fields when the fields are displays.

    - **initial**: The default value of the field.

    - **help_text**: The text displayed when a mouse hovers over the question mark next to the field.


Below is an example of a new input field type definition: which contains a natural number, a string and a list of strings.

::


    def get_domain_specific_schemas(self):
        schema_data = {
            u'%s/input/domain_specific' % NAMESPACE_PREFIX:
            [u'Domain-specific input field type',
             {
                 u'number_input':   {'type': models.ParameterName.NUMERIC,
                                     'subtype': 'natural',
                                     'description': 'Enter Number',
                                     'ranking': 0,
                                     'initial': 42,
                                     'help_text': 'The number needed for this computation',
                                     },
                u'string_input': {'type': models.ParameterName.STRING,
                                    'subtype': '',
                                    'description': 'Enter string',
                                    'ranking': 1,
                                    'initial': 'job scheme',
                                    'help_text': 'The scheme needed for this computaiton'},
                u'list_input': {'type': models.ParameterName.STRLIST,
                                    'choices': '[("option1", "Option 1"), ("option2", "Option 2")]',
                                    'subtype': '',
                                    'description': 'Choose your option',
                                    'ranking': 2,
                                    'initial' : '',
                                    'help_text': 'The list of options for the computation'},
             }
            ],
        }
        return schema_data


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






.. _examples:

Examples
~~~~~~~~

Here, we use the following examples to show the different features of a smart connector
and how a smart connector is defined and registered within a Chiminey server.

.. toctree::
    quick_example
    randnumcloud

