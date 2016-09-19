
.. _smart_connector_desc:

Smart Connector: the core concept within Chiminey
-------------------------------------------------

A **smart connector** is the core concept within  Chiminey that enables endusers to
perform complex computations on distributed computing facilities with minimal effort.
It  uses the abstractions provided by Chiminey to define  transparent automation and error handling of
complex  computations on the cloud and traditional HPC infrastructure.




Stage
"""""

A **stage** is a unit of computation within Chiminey. Each stage hast at least the following elements:

    - **validation:**
        Before the execution of a smart connector starts, the Chiminey server checks whether the constraints of all stages of the smart connector are met. This is done by invoking  ``input_valid(self, ...)`` method of each stage of the smart connector.

    - **pre-condition:**
        The Chiminey platform uses  pre-conditions to determine the stage that should be  executed next.  The Chiminey platform invokes the  method ``is_triggerred(self, ...)`` in order to check whether the  pre-condition  of a particular stage is met.

    - **action:**
        This is the main functionality of a stage. Such functionality includes creating virtual machines, waiting for computations to complete, and the like. Once the Chiminey platform determines the next stage to execute, the server executes the stage via  the ``process(self, ...)`` method.

    - **post-condition:**
        This is where the  new state of the smart connector job is written to a persistent storage upon the successful completion of  a stage execution. During the execution of a stage, the state of a smart connector job changes. This change is saved via the ``output(self, ...)`` method.



The relationship between smart connectors and stages
""""""""""""""""""""""""""""""""""""""""""""""""""""

A smart connector is composed of stages,
each stage  with  a unique functionality.
Following are the predefined stages that make up a smart connector (the predefined stages are located at ``chiminey/corestages``):

    - **parent:**
        Provides a handle to which all stages are within a smart connector are attached when a smart connector is registered within Chiminey.  Contains methods that are needed by two or more stages.

    - **configure:**
        Prepares scratch spaces, creates MyTardis experiments, ...

    - **create:**
        Creates virtual machines on cloud-based infrastructure.

    - **bootstrap:**
        Sets up the execution environment for the entire job, e.g. installs dependencies.

    - **schedule:**
        Sets up the execution environment for individual task, and schedules tasks to available resources. A job is composed of one or more tasks. This stage is especially important when the job has more than one task.

    - **execute:**
        Starts the execution of each task.

    - **wait:**
        Checks whether a task is completed or not. Collects the output of completed tasks.

    - **transform:**
        Prepares the input to the computation in the next iteration. Some smart connector jobs, for example :ref:`Hybrid Reverse Monte Carlo <hrmc>` simulations,   have more than one iterations. When all tasks in the  current iteration are completed and their corresponding output is collected, the transform stage prepares the input to  the upcoming tasks  in the next iteration.

    - **converge:**
        Checks whether convergence is reached, where a job has more than one iteration.  A convergence  is assumed to be reached when either  some criterion or  the maximum number of iterations is reached.

    - **destroy:**
        Terminates previously created virtual machines.



.. _create_sc:

Creating a smart connector
"""""""""""""""""""""""""""

Creating a smart connector involves completing three tasks:

  #. providing :ref:`the core functionality <sc_core_fcn>` of the smart connector,
  #. attaching :ref:`resources and optional non-functional properties <sc_attach_resources>`, and
  #. :ref:`registering <sc_registration>` the new smart connector with the Chiminey platform.


Each of the three tasks is discussed below by  creating an example smart connector. This  smart connector  generates a random number with a timestamp,  and then writes the output to a file.


**NB**: Login to the Chiminey docker container.

    - For Mac OS X and Windows users, open `Docker Quickstart Terminal`. For linux-based OS users, login to your machine and open a terminal.

    - Login to the chiminey docker container::

        $ cd docker-chiminey
        $ ./chimineyterm



.. _sc_core_fcn:

The Core Function
~~~~~~~~~~~~~~~~~

The core functionality of a smart connector is provided either via a :ref:`payload <payload>` or by overriding the ``run_task`` method of ``chiminey.corestages.execute.Execute`` class.
In this example, we use a minimal payload to provide the core functionality of this smart connector. Thus, we will prepare the following payload.

::

    payload_randnum/
    |--- process_payload
    │    |--- main.sh


Below is the content of main.sh::

  #!/bin/sh
  OUTPUT_DIR=$1
  echo $RANDOM > $OUTPUT_DIR/signed_randnum date > $OUTPUT_DIR/signed_randnum
  # --- EOF ---


Notice ``OUTPUT_DIR``. This is the path to the output directory, and thus Chiminey expects all outputs to be redirected to that location.
The contents of ``OUTPUT_DIR`` will be transferred to the output location at the end of each computation.


.. _sc_attach_resources:

Attaching resources and non-functional properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resources and non-functional properties are attached to a smart connector by overriding ``get_ui_schema_namespace`` method of ``chiminey.initialisation.coreinitial.CoreInitial`` class.
New domain-specific variables can be introduced via ``get_domain_specific_schemas`` method.  In this example, we will need to attached a unix compute resource for the computation, and
a storage resource for the output location. However, we will not add a non-functional property.

Under chiminey/, we create a python package `randnum`, and add ``initialise.py`` with the following content

::

    from chiminey.initialisation import CoreInitial
    from django.conf import settings
    class RandNumInitial(CoreInitial):
    def get_ui_schema_namespace(self):
            schemas = [
                    settings.INPUT_FIELDS[’unix’],
                    settings.INPUT_FIELDS[’output_location’],
    ] return schemas
    # ---EOF ---

**NB**: The list of available resources and non-functional properties is given by ``INPUT_FIELDS`` parameter in ``chiminey/settings_changeme.py``

.. _sc_registration:

Registration
~~~~~~~~~~~~~

The final step is registering the smart connector  with the Chiminey platform. The details of this smart connector will be added to the dictionary ``SMART CONNECTORS`` in ``chiminey/settings changeme.py``.
The details include a unique name (with no spaces), a python path to ``RandNumInitial`` class, the description of the smart connector, and the absolute path to the payload.

::

      "randnum": {
                 "name": "randnum",
                 "init": "chiminey.randnum.initialise.RandNumInitial",
                 "description": "Randnum generator, with timestamp",
                 "payload": "/opt/chiminey/current/payload_randnum"
      },


Finally, restart the Chiminey platform and then activate ``randnum`` smart connector. You need to exit the docker container in order to restart::

  $ exit
  $ sh restart
  $ ./activatesc randnum


Food for Thought
~~~~~~~~~~~~~
In the example above, we created  a  smart connector that generates  a random number on a unix-based machines. Even though the random number generator a simple
smart connector, the tasks that are involved in creating a smart connector for complex programs is similar. If your program can be executed on a cloud, HPC cluster, hadoop cluster, then this program can be packaged as a smart connector. The huge benefit of using the Chiminey platform to run your program is you don't need to worry about how to
manage the execution of your program on any of the provided compute resources.
You can run your program on different types of compute resources with minimal effort. For instance,  to generate random on a cloud-based virtual machine, we need
to change only one word in ``get_ui_schema_namespace method``. Replace ``unix`` by ``cloud``. Then, restart Chiminey, and activate your cloud-based random number generator.

Check the :ref:`various examples <examples>` are given in this documentation. These examples discuss the different types of compute and storage resources, and non-functional properties like reliability and parameter sweep. 
