
The MyTardis Random Number Smart Connector
==========================================

In this example, we create a smart connector that uses the MyTardis data curation system.


In this example, we create a  smart connector that generates a pair of random numbers on the cloud_.
This smart
connector creates a virtual machine (VM),
executes a number generator on the VM to produce two random numbers, transfers  the file that contains the random numbers to a user-designated
location, and pushes the results into MyTardis for visualisation.

We call this smart connector the *mytardis random number smart connector*.

- The **purpose** of this example is to create a smart connector that executes programs on the cloud and sends execution results to the mytardis system.

- The **source code** for this example is available at ``chiminey/examples/randnummytardis``.

- To add :ref:`external parameter sweep <external_parameter_sweep>` to this smart connector, see :ref:`quick example <sweep>`.


Requirements
------------

#. Installation and configuration of the Chiminey server on a virtual machine,
   according to the :ref:`Installation Guide <installation_guide>`.
#. Registration of a cloud computation platform, which is where the core
   functionality of a smart connector is executed within the Chiminey
   UI (see registering :ref:`Cloud Computation Platform <cloud_platform>`).
#. Registration of a storage platform, which is the destination of the
   smart connector output within the Chiminey UI. As with other storage
   platforms, the platform could be any unix server, again
   including the Chiminey server itself (see registering :ref:`Unix Storage Platform <unix_storage_platform>`).
#. Registration of a Mytardis storage platform, which is the destination of the smart
   connector output within the Chiminey UI (see registering :ref:`MyTardis Storage <mytardis_storage_platform>`).




Creating the MyTardis Random Number Smart Connector
---------------------------------------------------

Here, we create the MyTardis random number :ref:`smart connector <smart_connector_desc>`.
For this, we need to carry out the following steps, in order:

#. :ref:`prepare <prepare_payload_mytardis>` a payload

#. :ref:`define <define_cloud_randnum_mytardis_conn>`  the smart connector using the pre-defined core stages, and

#. :ref:`register  <register_smart_mytardis_conn_cloud>` the smart connector within Chiminey so it can be executed.



.. _prepare_payload_mytardis:

Preparing a Payload
~~~~~~~~~~~~~~~~~~~

We now discuss how to prepare a :ref:`payload <payload>` for the MyTardis random number smart connector.
This step is required because the computation platform of this smart connector is
a cloud infrastructure and :ref:`all cloud-based smart connectors must include their domain-specific executables in a payload <payload>`.


**NB:** The payload for the MyTardis random number smart connector is available at ``chiminey/examples/randnummytardis/payload_randnum``.

#. The Chiminey server expects  payloads to be under ``LOCAL_FILESYS_ROOT_PATH``, which is ``/var/chiminey/remotesys`` by default. A subdirectory can be created under ``LOCAL_FILESYS_ROOT_PATH`` to better organise payloads. On such occasions,  :ref:`the Chiminey server must be configured to point to the subdirectory <define_cloud_randnum_mytardis_conn>`. Let's now  create a subdirectory ``my_payloads``, and then put ``payload_randnum`` under it.

   ::

        mkdir -p /var/chiminey/remotesys/my_payloads
        cp -r  /opt/chiminey/current/chiminey/examples/randnummytardis/payload_randnum /var/chiminey/remotesys/my_payloads/


#. As recommended in :ref:`payload <payload>`, ``payload_template`` is used as the starting point to prepare ``payload_randnum``.   In order to satisfy   the requirements of this smart connector, ``start_running_process.sh`` will be changed.

    a. ``start_running_process.sh`` includes  the logic for generating the random numbers.
       As :ref:`expected by the Chiminey server <proc_running_script>`, the output of the program is redirected to
       ``chiminey``. Since this random generator is synchronous, the process ID is not  saved. Here is the content
       of ``start_running_process.sh``:

       ::

            #!/bin/sh
            python -c 'import random;  print random.random(); print random.random()'  >& chiminey/rand


    b. ``process_running_done.sh`` remains the same because the random number generating program is synchronous.

    c. ``start_bootstrap.sh`` and ``bootstrap_done.sh`` remain the same. This is because the random number
       generation depends only on ``python``, and the  included ``python`` in  linux-based OS  fulfills the requirement.

    d. ``start_process_schedule.sh`` and  ``start_running_process.sh`` remain the same because there is
       no process-level configuration requirement.



Customizing the Configure Stage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The customised configure stages, i.e., ``RandConfigure``, is available at ``chiminey/examples/randnummytardis/randconfigure.py``.


#. ``RandConfigure`` subclasses the core execute stage ``Configure``, which is located at ``chiminey/corestages/configure.py``.
   ``RandConfigure`` overwrites ``curate_data(self, ....)`` to include the code that generates an initial experiment in mytardis (it does nothing by default)

::

   def curate_data(self, run_settings, output_location, experiment_id):
       '''
          Creates experiment in MyTardis
       '''
       # Loading MyTardis credentials
       bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % SCHEMA_PREFIX)
       mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % SCHEMA_PREFIX)
       mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
       logger.debug("mytardis_settings=%s" % mytardis_settings)

       def _get_experiment_name(path):
           '''
               Return the name for MyTardis experiment
               e.g., if path='x/y/z', returns 'y/z'
           '''
           return str(os.sep.join(path.split(os.sep)[-2:]))

       # Creates new experiment if experiment_id=0
       # If experiment_id is non-zero, the experiment is updated
       experiment_id = mytardis.create_experiment(
           settings=mytardis_settings,  # MyTardis credentials
           exp_id=experiment_id,
           expname=_get_experiment_name(output_location),  # name of the experiment in MyTardis
           # metadata associated with the experiment
           # a list of parameter sets
           experiment_paramset=[
               # a new blank parameter set conforming to schema 'remotemake'
               mytardis.create_paramset("remotemake", []),
               # a graph parameter set
               mytardis.create_graph_paramset("expgraph",  # name of schema
                   name="randexp1",  # unique graph name
                   graph_info={"axes":["x", "y"], "legends":["Random points"]},  # information about the graph
                   value_dict={},  # values to be used in parent graphs if appropriate
                   value_keys=[["randdset/x", "randdset/y"]]),  # values from datasets to produce points in the graph
                          ])
       return experiment_id


The ``create_experiment`` command  creates or updates and experiment in a mytardis platform.  In this case, we either update the experiment with the ``experiment_id`` key, or creates a new experiment  and returns in the new experiment_id.

The experiment takes an ``exp-name' for the name of the experiment and optionally has the metadata that will be associated with the MyTardis experiment.

The ``experiment_paramset`` parameter is a list of parameter sets.  A parameterset either:

#. ``create_paramset``
   Creates a parameter set with an associated name and a specified set of parameter values (in this example useful for mytardis to indicate that the data in this experiment comes from a specific source).
#. ``create_graph_paramset``
  Creates a parameter set with a special fixed format that allows mytardis to create graphs in its output.

Below is the content of the ``RandConfigure`` class:

::

  import os
  import logging
  from chiminey.platform import manage
  from chiminey.corestages import Configure
  from chiminey import mytardis
  from chiminey.runsettings import getval

  logger = logging.getLogger(__name__)
  SCHEMA_PREFIX = "http://rmit.edu.au/schemas"


  class RandConfigure(Configure):
      '''
          Sets up output locations and credentials, MyTardis credentials,
          and creates experiment in MyTardis
      '''
      def curate_data(self, run_settings, output_location, experiment_id):
          '''
             Creates experiment in MyTardis
          '''
          # Loading MyTardis credentials
          bdp_username = getval(run_settings, '%s/bdp_userprofile/username' % SCHEMA_PREFIX)
          mytardis_url = getval(run_settings, '%s/input/mytardis/mytardis_platform' % SCHEMA_PREFIX)
          mytardis_settings = manage.get_platform_settings(mytardis_url, bdp_username)
          logger.debug("mytardis_settings=%s" % mytardis_settings)

          def _get_experiment_name(path):
              '''
                  Return the name for MyTardis experiment
                  e.g., if path='x/y/z', returns 'y/z'
              '''
              return str(os.sep.join(path.split(os.sep)[-2:]))

          # Creates new experiment if experiment_id=0
          # If experiment_id is non-zero, the experiment is updated
          experiment_id = mytardis.create_experiment(
              settings=mytardis_settings,  # MyTardis credentials
              exp_id=experiment_id,
              expname=_get_experiment_name(output_location),  # name of the experiment in MyTardis
              # metadata associated with the experiment
              # a list of parameter sets
              experiment_paramset=[
                  # a new blank parameter set conforming to schema 'remotemake'
                  mytardis.create_paramset("remotemake", []),
                  # a graph parameter set
                  mytardis.create_graph_paramset("expgraph",  # name of schema
                      name="randexp1",  # unique graph name
                      graph_info={"axes":["x", "y"], "legends":["Random points"]},  # information about the graph
                      value_dict={},  # values to be used in parent graphs if appropriate
                      value_keys=[["randdset/x", "randdset/y"]]),  # values from datasets to produce points in the graph
                             ])
          return experiment_id

Customizing the Transform Stage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The customised configure stages, i.e., ``RandTransform``, is available at ``chiminey/examples/randnummytardis/randtransform.py``.


#. ``RandTransform`` subclasses the core transform stage ``transform``, which is located at ``chiminey/corestages/transform.py``.
   ``RandTransform`` overwrites ``def curate_dataset(self, ....)``
   to include the code that generates an new dataset in an existing experiment in mytardis (it does nothing by default)

#. It takes ``experiment_id`` as the parameter which is the experiment id created in the RandExecute Stage.

#. After an initial preamble, the method traverses the directories of output to extract key data values from the datafiles (in this case the two random numbers from the ``rand`` file).  These are then passed into the mytardis ``create_datset`` method:

::

  experiment_id = mytardis.create_dataset(
      settings=all_settings, # MyTardis credentials
      source_url=process_output_url_with_cred,
      exp_id=experiment_id,
      dataset_name=_get_dataset_name, # the function that defines dataset name
      dataset_paramset=[
          # a new blank parameter set conforming to schema 'remotemake/output'
          mytardis.create_paramset("remotemake/output", []),
          mytardis.create_graph_paramset("dsetgraph", # name of schema
              name="randdset", # a unique dataset name
              graph_info={},
              value_dict={"randdset/x": x, "randdset/y": y},  # values to be used in experiment graphs
              value_keys=[]
              ),
          ]
      )

As with ``create_experiment`` this method takes an existing ``experiment_id`` and takes a dataset_name, however this is a function not a string, as it must be called after the initial setup of the dataset is complete.  Otherwise, as before, we use a set of dataset parameters, using the same methods, but we send the new ``x`` and ``y`` data points along as well to be interpreted by MyTardis.


Below is the content of the ``RandTransform`` class:

::

  import os
  import logging
  from chiminey.corestages import Transform
  from chiminey import mytardis
  from chiminey import storage
  from chiminey.runsettings import getval
  from chiminey.storage import get_url_with_credentials

  logger = logging.getLogger(__name__)
  SCHEMA_PREFIX = "http://rmit.edu.au/schemas"
  OUTPUT_FILE = "output"


  class RandTransform(Transform):
      '''
          Curates dataset into existing MyTardis experiment
      '''
      def curate_dataset(self, run_settings, experiment_id,
                         base_url, output_url, all_settings):
          '''
              Curates dataset
          '''
          # Retrieves process directories below the current output location
          iteration = int(getval(run_settings, '%s/system/id' % SCHEMA_PREFIX))
          output_prefix = '%s://%s@' % (all_settings['scheme'],
                                      all_settings['type'])
          current_output_url = "%s%s" % (output_prefix, os.path.join(os.path.join(
              base_url, "output_%s" % iteration)))
          (scheme, host, current_output_path, location, query_settings) = storage.parse_bdpurl(output_url)
          output_fsys = storage.get_filesystem(output_url)
          process_output_dirs, _ = output_fsys.listdir(current_output_path)

          # Curates a dataset with metadata per process
          for i, process_output_dir in enumerate(process_output_dirs):
              # Expand the process output directory and add credentials for access
              process_output_url = '/'.join([current_output_url, process_output_dir])
              process_output_url_with_cred = get_url_with_credentials(
                      all_settings,
                      process_output_url,
                      is_relative_path=False)
              # Expand the process output file and add credentials for access
              output_file_url_with_cred = storage.get_url_with_credentials(
                  all_settings, '/'.join([process_output_url, OUTPUT_FILE]),
                  is_relative_path=False)
              try:
                  output_content = storage.get_file(output_file_url_with_cred)
                  val1, val2 = output_content.split()
              except (IndexError, IOError) as e:
                  logger.warn(e)
                  continue
              try:
                  x = float(val1)
                  y = float(val2)
              except (ValueError, IndexError) as e:
                  logger.warn(e)
                  continue

              # Returns the process id as MyTardis dataset name
              all_settings['graph_point_id'] = str(i)
              def _get_dataset_name(settings, url, path):
                  return all_settings['graph_point_id']

              # Creates new dataset and adds to experiment
              # If experiment_id==0, creates new experiment
              experiment_id = mytardis.create_dataset(
                  settings=all_settings, # MyTardis credentials
                  source_url=process_output_url_with_cred,
                  exp_id=experiment_id,
                  dataset_name=_get_dataset_name, # the function that defines dataset name
                  dataset_paramset=[
                      # a new blank parameter set conforming to schema 'remotemake/output'
                      mytardis.create_paramset("remotemake/output", []),
                      mytardis.create_graph_paramset("dsetgraph", # name of schema
                          name="randdset", # a unique dataset name
                          graph_info={},
                          value_dict={"randdset/x": x, "randdset/y": y},  # values to be used in experiment graphs
                          value_keys=[]
                          ),
                      ]
                  )
          return experiment_id

.. _define_cloud_randnum_mytardis_conn:

Defining the MyTardis Random Number Smart Connector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The   definition of this smart connector, i.e., ``RandNumMyTardisInitial``, is available at ``chiminey/examples/randnummytardis/initialise.py``.

#. ``RandNumMyTardisInitial`` subclasses ``CoreInitial``, which is located at ``chiminey/initialise/coreinitial.py``.
   ``RandNumMyTardisInitial``  overwrites ``get_updated_configure_params(self)``, ``get_updated_bootstrap_params(self)``, ``get_updated_transform_params(self)`` and  ``get_ui_schema_namespace(self)``.

#. ``get_updated_configure_params(self)`` configures a subclass of the Configure corestage for specifying initial experiments for mytardis.

#. ``get_updated_bootstrap_params(self)`` updates settings to point the Chiminey server to the location of
   the new payload. The location of any payload is given relative to ``LOCAL_FILESYS_ROOT_PATH``. Since we :ref:`previously <prepare_payload_mytardis>`  copied ``payload_randnum`` to  ``LOCAL_FILESYS_ROOT_PATH/my_payloads/payload_randnum``, the location of the payload is ``my_payloads/payload_randnum``.

#. ``get_updated_transform_params(self)`` configures a subclass of the Transform corestage for specifying datasets for mytardis.

#. The new ``get_ui_schema_namespace(self)`` contains four schema namespaces that represent four types
   of input fields for specifying the name of a cloud-based computation platform, the maximum and minimum number of VMs
   needed for the job, the name for the mytardis platform and an output location (see :ref:`chiminey_ui`).

Below is the content of ``RandNumMyTardisInitial``.

::


    from chiminey.initialisation import CoreInitial

    class RandNumMyTardisInitial(CoreInitial):
        def get_updated_configure_params(self):
            package = "chiminey.examples.randnummytardis.randconfigure.RandConfigure"
            settings = {
                u'http://rmit.edu.au/schemas/system':
                    {
                        u'random_numbers': 'file://127.0.0.1/randomnums.txt'
                    },
            }
            return {'package': package, 'settings': settings}

        def get_updated_bootstrap_params(self):
            settings = {
                    u'http://rmit.edu.au/schemas/stages/setup':
                        {
                            u'payload_source': 'local/payload_randnum',

                        },
                }
            return {'settings': settings}

        def get_updated_transform_params(self):
            return {'package': "chiminey.examples.randnummytardis.randtransform.RandTransform"}

        def get_ui_schema_namespace(self):
            RMIT_SCHEMA = "http://rmit.edu.au/schemas"
            schemas = [
                    RMIT_SCHEMA + "/input/system/compplatform/cloud",
                    RMIT_SCHEMA + "/input/system/cloud",
                    RMIT_SCHEMA + "/input/location/output",
                    RMIT_SCHEMA + "/input/mytardis"
                    ]
            return schemas



.. _register_smart_mytardis_conn_cloud:

Registering the MyTardis Random Number Smart Connector within Chiminey
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A smart connector can be registered within the Chiminey server in various ways. Here,
a `Django management command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#management-commands-and-locales>`__ is used.
``chiminey/smartconnectorscheduler/management/commands/randnummytardis.py`` contains the Django management command for registering the cloud
random number smart connector. Below is the full content.


::

    from django.core.management.base import BaseCommand
    from chiminey.smartconnectorscheduler import models
    from chiminey.examples.randnummytardis.initialise import RandNumMyTardisInitial

    logger = logging.getLogger(__name__)

    MESSAGE = "This will add a new directive to the catalogue of available connectors.  Are you sure [Yes/No]?"



    class Command(BaseCommand):
        """
        Load up the initial state of the database (replaces use of
        fixtures).  Assumes specific structure.
        """

        args = ''
        help = 'Setup an initial task structure.'

        def setup(self):
            confirm = raw_input(MESSAGE)
            if confirm != "Yes":
                print "action aborted by user"
                return

            directive = RandNumMyTardisInitial()
            directive.define_directive(
                'randnum_mytardis', description='RandNum MyTardis')
            print "done"


        def handle(self, *args, **options):
            self.setup()
            print "done"


#. When registering a smart connector, a **unique name** must be provided. In this case, *randnum_mytardis*. If a smart connector exists with the same name, the command will be ignored.

#. A short **description** is also needed. In this case, *RandNum MyTardis*.  Both the unique name and the description will be displayed on the Chiminey UI.



#. Execute the following commands on the Chiminey server terminal

   ::

        sudo su bdphpc
        cd /opt/chiminey/current
        bin/django randnummytardis
        Yes

#. Visit your Chiminey web page; click ``Create Job``. You should see ``RandNum MyTardis`` under ``Smart Connectors`` menu.


.. _test_randnummytardis:

Testing the MyTardis Random Number Smart Connector
""""""""""""""""""""""""""""""""""""""""""""""""""

Now, test the correct definition and registration of the
MyTardis random number smart connector.  For this, you will :ref:`submit  <test_submit_job_cloud>` a MyTardis random number smart connector job,
:ref:`monitor <test_monitor_job_cloud>`  the job,
and :ref:`view <test_view_output_cloud>` the output of the job.

.. _test_submit_job_mytardis:

Submit a MyTardis random number smart connector job
'''''''''''''''''''''''''''''''''''''''''''''''''''

See :ref:`Job Submission <submit_job>` for details.


.. _test_monitor_job_mytardis:

Monitor the progress of the job
'''''''''''''''''''''''''''''''

See :ref:`Job Monitoring <monitor_job>` for details.


.. _test_view_output_mytardis:

View job output
'''''''''''''''

When the job is completed, view the two generated random numbers

#. Login to your storage platform
#. Change directory to the root path of your storage platform
#. The output is located under *smart_connector_uniquenameJOBID*, e.g. randnum_mytardis217
