The Random Number Smart Connector for Non-Cloud Execution
---------------------------------------------------------

In this example, we create a basic smart connector that generates a
random number on a compute cluster node (or the Chiminey server machine,
for simplicity), saves the number to a file, and then transfers the file
to a provided output location. This smart connector will be known as the
Random Number Smart Connector.

Requirements
~~~~~~~~~~~~

1. Installation and configuration of the Chiminey server on a VM,
   according to `Installation
   Guide <https://github.com/chiminey/chiminey/blob/master/docs/installation.rst>`__.
2. Registration of a computation platform, which is where the core
   functionality of a smart connector is executed within the Chiminey
   UI. For this example, the platform could be any unix server,
   including the Chiminey server itself. (see `Registering Computation
   Platforms,
   Cluster/Unix </chiminey/chiminey/wiki/Enduser-Manual#wiki-cluster_unix_platform>`__).
3. Registration of a storage platform, which is the destination of the
   smart connector output within the Chiminey UI. As for the computation
   platform above, the platform could be any unix server, again
   including the Chiminey server itself. (see `Registering Storage
   Platform,
   Unix </chiminey/chiminey/wiki/Enduser-Manual#wiki-unix_storage_platform>`__).

Creating the Random Number Smart Connector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A smart connector is composed of at least seven predefined core stages:
configure, create, bootstrap, schedule, execute, wait and destroy.
Depending of the expected functionality of a smart connector, one or
more of the core stages may need to be customised, and/or other stages
may need to be added. All core stages are located under
chiminey/corestages.

In general, creating a smart connector involves

-  customising existing and/or adding new stages as needed,
-  defining the smart connector based on these stages, and
-  registering the smart connector within chiminey.

Specifically, creating the random number smart connector requires

1. `customizing the execute stage <#customize_execute_stage>`__,
2. `defining the smart connector <#define_smart_conn>`__ with the new
   execute stage and the pre-defined core stages, and
3. `registering the smart connector within
   Chiminey <#register_smart_conn>`__, so it can be executed.
4. In this example, we also show how to add a `sweep functionality to a
   smart connector <#sweep>`__.

 #### 1. Customizing the Execute Stage

The core execute stage (located at chiminey/corestages/execute.py)
includes all the basic functionality that a smart connector's execute
stage requires. The random number smart connector in this example
overrides only a single method of the execute stage, specifically
``run_task``.

    1. Create an empty chimney/randomnumber/randexecute.py
    2. Make a subclass of Execute called RandExecute, located in
       randexecute.py
    3. Override run\_task()in RandExecute class:
    4. Define a command that generates a random number and saves the
       result to a file, e.g. python -c 'import random; print
       random.random()' > file
    5. Use the run\_command() from chiminey/compute package to run this
       command above
    6. The Chimney platform expects the output of a computation to be in
       a specific location. Use ``get_process_output_path()`` to
       retrieve the path to which the output of your computation should
       be sent. For this example, this path is not created
       automatically, therefore must be created prior to generating
       results.

Below is the content of the ``RandExecute`` class, in
chimney/randomnumber/randexecute.py

::

    from chiminey.corestages import Execute
    from chiminey.compute import run_command

    class RandExecute(Execute):
        def run_task(self, ip_address, process_id, connection_settings, run_settings):
            filename = 'rand'
            output_path = self.get_process_output_path(run_settings, process_id, connection_settings)
            command = "mkdir -p %s; cd %s ; python -c 'import random;"\ 
                  "print random.random()' > %s" \
                  % (output_path, output_path, filename)
            output, err = run_command(command, ip_address,connection_settings)

 #### 2. Defining the Random Number Smart Connector

The process of defining a smart connector, in general, involves \*
defining stages: which require specifying a name and the full package
path to the stage's source code, and optionally setting constants that
are needed during the execution of that stage; \* assembling predefined
stages under a common parent stage; and \* attaching relevant UI form
fields to the smart connector (for user input).

Specifically, defining the random number smart connector involves, \*
`redefining the execute stage <#redefine_exec_stage>`__ \* `attaching UI
form fields <#attach_form_fields>`__

 ##### Redefining the execute stage > 1. Create an empty
chiminey/smartconnectorscheduler/management/commands/randinitial.py > 1.
Make a subclass of ``CoreInitial`` class called RandInitial, contained
in randinitial.py. Defining a smart connector requires inheriting from
the generic connector in the ``CoreInitial`` class, which is located at
chiminey/smartconnectorscheduler/management/commands/coreinitial.py. >
1. Redefine the execute stage: > 1. Since the execute stage is
overridden by the random number smart connector, the definition of the
execute stage should similarly be overridden in the class RandInitial to
point to the RandExecute class. Defining the execute stage requires a)
the full package path to the stage's source code, i.e.,
``chimney.randomnumber.randexecute.RandExecute``, b) a name such as
``randexecute``, and c) set constants for the parameters:
``payload_cloud_dirname``, ``compile_file`` and ``retry_attempt``\ s.

Below is the new definition of the execute stage of the random number
smart connector:

::

    #overwrites the core execute stage definition
    def define_execute_stage(self):
        execute_package = "chimney.randomnumber.randexecute.RandExecute"
        execute_stage, _ = models.Stage.objects.get_or_create(
                           name="randexecute", package=execute_package,
                           parent=self.define_parent_stage(),
                           defaults={'description': "This is the rand execute stage", 
                           'order': 11})
        execute_stage.update_settings(
            {
            u'http://rmit.edu.au/schemas/stages/run':
                {
                    u'payload_cloud_dirname': '',
                    u'compile_file': '',
                    u'retry_attempts': 3,
                },
            })

 ##### Attaching UI form fields

There are two types of input fields that are needed to submit a random
number smart connector job, i.e., the `name of the computation
platform </chiminey/chiminey/wiki/Types-of-Input-Form-Fields#wiki-computation_platform>`__
and `output
location </chiminey/chiminey/wiki/Types-of-Input-Form-Fields#wiki-location>`__.
Below is shown how the input fields are attached

::

    def attach_directive_args(self, new_directive):
        RMIT_SCHEMA = "http://rmit.edu.au/schemas"
        schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/system/compplatform")
        das, _ = models.DirectiveArgSet.objects.get_or_create(
            directive=new_directive, order=1, schema=schema)
        schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/location/output")
        das, _ = models.DirectiveArgSet.objects.get_or_create(
            directive=new_directive, order=2, schema=schema)

Below is the full content of the RandInitial class found in
chiminey/smartconnectorscheduler/management/commands/randinitial.py

::

    from chiminey.smartconnectorscheduler import models
    from chiminey.smartconnectorscheduler.management.commands import coreinitial

    class RandInitial(coreinitial.CoreInitial):
        #overwrites the core execute stage definition
        def define_execute_stage(self):
            execute_package = "chimney.randomnumber.randexecute.RandExecute"
            execute_stage, _ = models.Stage.objects.get_or_create(
                           name="randexecute", package=execute_package,
                           parent=self.define_parent_stage(),
                           defaults={'description': "This is the rand execute stage", 
                           'order': 11})
            execute_stage.update_settings(
              {
               u'http://rmit.edu.au/schemas/stages/run':
                 {
                    u'payload_cloud_dirname': '',
                    u'compile_file': '',
                    u'retry_attempts': 3,
                 },
              })
       # attaches computation platform name and output location to UI
       def attach_directive_args(self, new_directive):
           RMIT_SCHEMA = "http://rmit.edu.au/schemas"
           schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/system/compplatform")
           das, _ = models.DirectiveArgSet.objects.get_or_create(
               directive=new_directive, order=1, schema=schema)
           schema = models.Schema.objects.get(namespace=RMIT_SCHEMA + "/input/location/output")
           das, _ = models.DirectiveArgSet.objects.get_or_create(
               directive=new_directive, order=2, schema=schema)

 #### 3. Registering the Random Number Smart Connector within Chiminey

A smart connector can be registered within the Chiminey server in
various ways. Here, a `Django management
command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#management-commands-and-locales>`__
is used.

    Append the following class to
    chiminey/smartconnectorscheduler/management/commands/randinitial.py

::

    from django.core.management.base import BaseCommand

    class Command(BaseCommand):
        def handle(self, *args, **options):
            smart_connector_name = 'random_number'
            directive = RandInitial()
            directive.define_directive(smart_connector_name, 
                description='Random Number Smart Connector')
            print "done"

    Execute the following commands in the chiminey server terminal

::

    cd /opt/chiminey/current
    sudo su bdphpc
    bin/django randinitial

    Visit your Chiminey front page Click 'Create Jobs'. You should see
    'Random Number Smart Connector' under 'Smart Connectors' menu.

Figure. The Random Number Smart Connector |Random Number Smart
Connector|

Testing the Random Number Smart Connector
'''''''''''''''''''''''''''''''''''''''''

Submitting a new job
                    

    1. Select a Cluster/Unix computation platform from the drop down
       'Computation Platform Name'
    2. Enter a Unix storage platform name and optionally enter a path
       offset from the storage platform's root path.
    3. Click 'Submit Job', then click 'OK' ; the smart connector is now
       executing!
    4. Monitor the progress of the submitted job from 'Jobs' page

Figure. Monitoring a random number smart connector job |Monitoring a
random number smart connector job|

Viewing the job output
                      

The job is completed when the "Iteration:Current" column of 'Jobs' page
displays "1: waiting 1 processes (1 completed, 0 failed)"

    1. Login to your storage platform
    2. Change directory to the root path of your storage platform
    3. The output is located under smart\_connector\_nameJOBID, e.g.
       random\_number560

 #### 4. Adding a Parameter Sweep to the Random Number Smart Connector

Parameter sweep is used to create multiple jobs, each with its set of
parameter values (see `Parameter
Sweep </chiminey/chiminey/wiki/Types-of-Input-Form-Fields#wiki-sweep>`__
for details). This feature can be added to a smart connector by turning
the sweep flag on during the `registration of the smart
connector <#register_smart_conn>`__.

    Below is the Command class with the sweep flag on.

::

    from django.core.management.base import BaseCommand

    class Command(BaseCommand):
        def handle(self, *args, **options):
            smart_connector_name = 'random_number'
            directive = RandInitial()
            directive.define_directive(smart_connector_name, 
                description='Random Number Smart Connector', sweep=True)
            print "done"

    Rexecute the following commands in the chiminey server terminal

::

    cd /opt/chiminey/current
    sudo su bdphpc
    bin/django randinitial

    Visit your Chiminey front page Click 'Create Jobs'. You should see
    'Sweep Random Number Smart Connector' under 'Smart Connectors' menu.

Figure. The Sweep Random Number Smart Connector |Random Number Smart
Connector|

Testing the Sweep Random Number Smart Connector
'''''''''''''''''''''''''''''''''''''''''''''''

Submitting a sweep job
                      

    1. Select a Cluster/Unix computation platform from the drop down
       'Computation Platform Name'
    2. Enter a Unix storage platform name and optionally enter a path
       offset from the storage platform's root path.
    3. Enter your sweep map e.g. {"var": [1,2]} to create two jobs
    4. Click 'Submit Job', then click 'OK' ; the smart connector is now
       executing!
    5. Monitor the progress of the submitted job from 'Jobs' page. Sweep
       jobs create sub-jobs which can be seen in the screenshot.

Figure. Monitoring a sweep random number smart connector job |Monitoring
a sweep random number smart connector job|

Viewing the job output
                      

The job is completed when the "Iteration:Current" column of 'Jobs' page
displays "1: waiting 1 processes (1 completed, 0 failed)"

    1. Login to your storage platform
    2. Change directory to the root path of your storage platform
    3. The output is located under sweep\_smart\_connector\_nameJOBID,
       e.g. sweep\_random\_number561/

.. |Random Number Smart Connector| image:: images/quick_example/create2_random_sc.png
.. |Monitoring a random number smart connector job| image:: images/quick_example/monitor_random_sc.png
.. |Random Number Smart Connector| image:: images/quick_example/create_sweep_random_sc.png
.. |Monitoring a sweep random number smart connector job| image:: images/quick_example/monitor_sweep_random_sc.png
