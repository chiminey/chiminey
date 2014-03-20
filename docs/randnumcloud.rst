    .. _cloud: http://aws.amazon.com/what-is-cloud-computing/

=======================================
The Cloud Random Number Smart Connector
=======================================

In this example, we create a  smart connector that generates a pair of random numbers on the cloud_.
We call this smart connector the *cloud random number smart connector*. This smart
connector creates a virtual machine (VM),
executes a number generator on the VM to produce two random numbers,
and then transfers  the file that contains the random numbers to a user-designated
location.

    - The **source code** for this example is available at ``chiminey/examples/randnumcloud``.

    - The **purpose** of this example is to show how to create a smart connector that executes programs on the cloud_.


Requirements
------------

1. Installation and configuration of the Chiminey server on a virtual machine,
   according to the :ref:`Installation Guide <installation_guide>`.
2. Registration of a cloud computation platform, which is where the core
   functionality of a smart connector is executed within the Chiminey
   UI. For this example, the platform could be any unix server,
   including the Chiminey server itself. (see registering :ref:`Cloud Computation Platform <cloud_platform>`).
3. Registration of a storage platform, which is the destination of the
   smart connector output within the Chiminey UI. As with other storage
   platforms, the platform could be any unix server, again
   including the Chiminey server itself. (see registering :ref:`Unix Storage Platform <unix_storage_platform>`).




Creating the Cloud Random Number Smart Connector
    ------------------------------------------------
Here, we a create the cloud random number :ref:`smart connector <smart_connector_desc>`.
For that, we need to carry out the following steps, in order:

1. :ref:`prepare <prepare_payload_cloud>` a payload

2. :ref:`define <define_cloud_randnum_conn>`  the smart connector using the pre-defined core stages, and

3. :ref:`register  <register_smart_conn_cloud>` the smart connector within Chiminey so it can be executed.







.. _prepare_payload_cloud:

I. Preparing Payload
~~~~~~~~~~~~~~~~~~~~

:ref:`payload <payload>`

1. edit files

2. copy to under LOCAL_FILESYS_ROOT_PATH, which is by default "/var/chiminey/remotesys"

.. _define_cloud_randnum_conn:


..  Creating the Cloud Random Number Smart Connector
    ------------------------------------------------
    Here, we a create the cloud random number :ref:`smart connector <smart_connector_desc>`.
    For that, we need to carry out the following steps, in order:

    1. :ref:`prepare <prepare_payload_cloud>` payload

    2. :ref:`define <define_cloud_randnum_conn>`  the smart connector using the pre-defined core stages, and

    3. :ref:`register  <register_smart_conn_cloud>` the smart connector within Chiminey so it can be executed.



    .. _prepare_payload_cloud:

    I. Preparing Payload
    ~~~~~~~~~~~~~~~~~~~~

    :ref:`payload <payload>`

    1. edit files

    2. copy to under LOCAL_FILESYS_ROOT_PATH, which is by default "/var/chiminey/remotesys"

    .. _define_cloud_randnum_conn:

    II. Defining the Cloud Random Number Smart Connector
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The new  definition of this smart connector, i.e., ``RandNumCloudInitial``, is available at ``chiminey/examples/randnumcloud/initialise.py``

    1. ``RandNumCloudInitial`` subclasses ``CoreInitial``, which is located at ``chiminey/initialise/coreinitial.py``.  ``RandNumCloudInitial``  overwrites ``get_updated_bootstrap_params(self)`` and  ``get_ui_schema_namespace(self)``.

    2. payload .... In the :ref:`previous step  <customize_execute_stage>`, the execute stage is customised. Therefore, ``get_updated_execute_params(self)`` updates the package path  to point to the customised execute stage class, which is
        ``chiminey.examples.randnumunix.randexexute.RandExecute``.

    3. The new ``get_ui_schema_namespace(self)`` contains two schema namespaces that represent three types of input fields:

        a. *RMIT_SCHEMA + "/input/system/compplatform"* for specifying the name of the `computation platform <https://github.com/chiminey/chiminey/wiki/Types-of-Input-Form-Fields#computation_platform>`__,
        b. *RMIT_SCHEMA + "/input/system/cloud"* for specifying the `maximum and minimum number of VMs <https://github.com/chiminey/chiminey/wiki/Types-of-Input-Form-Fields#cloud_resource>`__  needed for the job, and
        c. *RMIT_SCHEMA + "/input/location/output"* for specifying the `output location <https://github.com/chiminey/chiminey/wiki/Types-of-Input-Form-Fields#location>`__.

    Below is the content of ``RandNumCloudInitial``.

    ::

        from chiminey.initialisation import CoreInitial

        class RandNumCloudInitial(CoreInitial):
            def get_updated_bootstrap_params(self):
                settings = {
                        u'http://rmit.edu.au/schemas/stages/setup':
                            {
                                u'payload_source': 'local/payload_randnum',
                                u'payload_destination': 'randnum_dest',
                                u'payload_name': 'process_payload',
                                u'filename_for_PIDs': 'PIDs_collections',
                            },
                    }
                return {'settings': settings}

            def get_ui_schema_namespace(self):
                RMIT_SCHEMA = "http://rmit.edu.au/schemas"
                schemas = [
                        RMIT_SCHEMA + "/input/system/compplatform",
                        RMIT_SCHEMA + "/input/system/cloud",
                        RMIT_SCHEMA + "/input/location/output",
                        ]
                return schemas

    .. _register_smart_conn_cloud:

    III. Registering the Cloud Random Number Smart Connector within Chiminey
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A smart connector can be registered within the Chiminey server in various ways. Here,
    a `Django management command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#management-commands-and-locales>`__ is used.
    ``chiminey/smartconnectorscheduler/management/commands/randnumcloud.py`` contains the Django management command for registering the cloud
    random number smart connector.

    1. When registering a smart connector, a **unique name** must be provided. In this case, *randnum_cloud*. If a smart connector exists with the same name, the command will be ignored.

    2. A short **description** is also needed. In this case, *RandNum Cloud*.  Both the unique name and the description will be displayed on the Chiminey UI.


    ::

        from django.core.management.base import BaseCommand
        from chiminey.examples.randnumcloud.initialise import RandNumCloudInitial

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

                directive = RandNumCloudInitial()
                directive.define_directive(
                    'randnum_cloud', description='RandNum Cloud')
                print "done"


            def handle(self, *args, **options):
                self.setup()
                print "done"



    3. Execute the following commands on the Chiminey server terminal

    ::

        cd /opt/chiminey/current
        sudo su bdphpc
        bin/django randnumcloud
        Yes

    4. Visit your Chiminey web page; click ``Create Job``. You should see ``RandNum Cloud`` under ``Smart Connectors`` menu.


    .. figure:: img/quick_example/create_randnumcloud.png
        :align: center
        :alt: The Cloud Random Number Smart Connector
        :figclass: align-center

        Figure. The Cloud Random Number Smart Connector


    .. _test_randnumcloud:

    Testing the Cloud Random Number Smart Connector
    """""""""""""""""""""""""""""""""""""""""""""""

    Now, test the correct definition and registration of the
    cloud random number smart connector.  For this, you will :ref:`submit  <test_submit_job_cloud>` a cloud random number smart connector job,
    :ref:`monitor <test_monitor_job_cloud>`  the job,
    and :ref:`view <test_view_output_cloud>` the output of the job.

    .. _test_submit_job_cloud:

    Submit a cloud random number smart connector job
    ''''''''''''''''''''''''''''''''''''''''''''''''

    See :ref:`Job Submission <submit_job>` for details.

    .. figure:: img/quick_example/submit_randnumcloud.png
        :align: center
        :alt: A cloud random number smart connector job
        :figclass: align-center

        Figure. A cloud random number smart connector job

    .. _test_monitor_job_cloud:

    Monitor the progress of the job
    '''''''''''''''''''''''''''''''

    See :ref:`Job Monitoring <monitor_job>` for details.

    .. figure:: img/quick_example/completed_randnumcloud.png
        :align: center
        :alt: The cloud random number smart connector job is completed
        :figclass: align-center

        Figure. The cloud random number smart connector job is completed


    .. _test_view_output_cloud:

    View job output
    '''''''''''''''

    When the job is completed, view the two generated random numbers

        a. Login to your storage platform
        b. Change directory to the root path of your storage platform
        c. The output is located under *smart_connector_uniquenameJOBID*, e.g. randnum_cloud180
