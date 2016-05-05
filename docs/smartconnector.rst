.. _smart_connector_desc:

Smart Connector: the core concept within Chiminey
-------------------------------------------------

A **smart connector** is the core concept within  Chiminey that enables endusers to
perform complex computations on distributed computing facilities with minimal effort.
It  uses the abstractions provided by Chiminey to define  transparent automation and error handling of
complex  computations on the cloud and traditional HPC infrastructure.

.. toctree::
    :hidden:

    sc_create



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
