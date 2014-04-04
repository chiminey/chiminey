.. _manage_job:

Job Management
==============

The end-user  submits, monitors and terminates jobs via the Chiminey UI.

.. _submit_job:

Job Submission
--------------


Follow the steps below

#. Navigate to the Chiminey server homepage
#. Log in with credentials
#. Click ``Create Job`` from the menu bar
#. Select the smart connector from the list of smart connectors
#. Enter the values for the parameters of the selected smart connector.
   Parameters of any smart connector fall into either of the following types: *Computation platform, Cloud resource, Location, Reliability, MyTardis, Parameter Sweep*
   and  *Domain-specific*. See :ref:`form_field_types` for detailed discussion about these parameter types.
#. Click ``Submit Job`` button, then ``OK``


.. figure:: img/enduser_manual/submit.png
    :align: center
    :alt:   Submitting a job
    :figclass: align-center

    Figure.  Submitting a job


.. _monitor_job:

Job Monitoring
--------------


Once a job is submitted, the end-user can monitor the status of the job.

#. Submit a job (see :ref:`submit_job`)
#. Click ``Jobs``. A job status summary of all jobs will be displayed. The most recently submitted job is displayed at the top.
#. Click ``Info`` button next to each job to view a detailed status report.
#. A job is completed when the ``Iteration:Current`` column of ``Jobs`` page displays  ``x: finished``, where ``x`` is the last iteration number.


.. figure:: img/enduser_manual/monitor.png
    :align: center
    :alt:   Monitoring a job
    :figclass: align-center

    Figure.  Monitoring a job



.. _terminate_job:

Job Termination
---------------


The end-user can terminate already submitted jobs.

#. Submit a job (see :ref:`submit_job`)
#. Click ``Jobs`` to view all submitted jobs.
#. Check the box at the end of the status summary of each job that you wish terminate.
#. Click ``Terminate selected jobs`` button. The termination of the
   selected jobs will be scheduled. Depending on the current
   activity of each job, terminating one job may take longer than
   the other.



.. figure:: img/enduser_manual/terminate.png
    :align: center
    :alt:   Terminating a job
    :figclass: align-center

    Figure.  Terminating a job

