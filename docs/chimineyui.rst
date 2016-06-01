
.. _chiminey_ui:

Chiminey User Interface
~~~~~~~~~~~~~~~~~~~~~~~

The Chiminey platform  automatically generates a job submission web page for each smart connector.
However, this web page contains only a drop down menu of :ref:`presets <manage_presets>`. The web page
will also
contain a :ref:`parameter sweep <parametersweep>`
input field for smart connectors with a sweep feature.
Since these two input fields are not sufficient to submit a job,
the developer should specify the input fields that are needed to submit
a particular smart connector job.
This is done during the :ref:`definition of the smart connector <constrtuct_smart_conn_ui>`.


Within the Chiminey platform, there are various :ref:`input field types <chiminey_ui>`, organised in groups like
compute resource variables, location variables and domain-specific variables.
The input fields, except the domain-specific ones, are provided via ``INPUT_FIELDS`` parameter in ``chiminey/settings_changeme.py``.
The following table shows the list of input field types and their description.


      +----------------------------+-------------------------------------------------+
      |      Input Field Type      |            Description                          |
      +============================+=================================================+
      |``unix``                    | | Dropdown menu containing the registered       |
      |                            | | HPC compute resources                         |
      +----------------------------+-------------------------------------------------+
      |``cloud``                   | | Dropdown menu of registered cloud resources,  |
      |                            | | number of VMs to be used for the job          |
      +----------------------------+-------------------------------------------------+
      |``hadoop``                  | | Dropdown menu of registered hadoop clusters   |
      +----------------------------+-------------------------------------------------+
      |``output_location``         | | Dropdown menu of registered storage resources |
      |                            | | (i.e. remote file system) with root path,     |
      |                            | | and a text field for specifying directories   |
      |                            | | under the root path.                          |
      +----------------------------+-------------------------------------------------+
      |``input_location``          | | Same as output location.                      |
      +----------------------------+-------------------------------------------------+
      |``location``                | | Input and output location                     |
      +----------------------------+-------------------------------------------------+
      |``reliability``             | | Set of fields to control the degree of the    |
      |                            | | provided fault tolerance  support             |
      +----------------------------+-------------------------------------------------+
      |``hrmclite``                | | Domain-specific input fields needed           |
      |                            | | to run :ref:`HRMCLite <hrmclite_sc>` jobs     |
      +----------------------------+-------------------------------------------------+
      |``wordcount``               | | Domain-specific input fields needed to run    |
      |                            | | :ref:`wordcount <wordcount_sc>` jobs          |
      +----------------------------+-------------------------------------------------+





.. _constrtuct_smart_conn_ui:

Constructing Smart Connector Input Fields
"""""""""""""""""""""""""""""""""""""""""

Here, we see how to include the input fields that are needed for submitting a smart connector job.
:ref:`When a smart connector is created <create_sc>`, one of the tasks is   attaching resources and non-functional properties via  input field types.
This task is done by overriding  ``get_ui_schema_namespace(self)`` of the ``CoreInitial`` class.
The ``CoreInitial`` class is available at ``chiminey/initialisation/coreinitial``.

Suppose the new smart connector is cloud-based and writes its output to a unix server.
Therefore, the job submission page of this smart connector must include two input field types that
enables end-users  to provide  a)
a cloud-based compute resource  and b) an output location. Suppose ``CloudSCInitial`` extends the ``CoreInitial`` class:

::

      from chiminey.initialisation import CoreInitial
      from django.conf import settings
      class CloudSCInitial(CoreInitial):
      def get_ui_schema_namespace(self):
          schemas = [
                  settings.INPUT_FIELDS['cloud'],
                  settings.INPUT_FIELDS['output_location'],
      ] return schemas

      # ---EOF ---



.. _domain_specific_input_fields:

Including domain-specific input fields
''''''''''''''''''''''''''''''''''''''

Input field types that are included within the Chiminey platform are generic and are included within the platform. However
 domain-specific input fields must be defined when needed. A domain-specific input field type is provided by overriding  ``get_domain_specific_schemas(self)``
 of the  ``CoreInitial`` class. This method will return a  list  of two elements:

 #.  The description of the input field type e.g. `HRMCLite Smart Connector`

 #.  A dictionary whose keys are the names of domain-specific input fields, their values are dictionaries  with the following keys:

        - **type**:  There are three types of input fields: *numeric* (models.ParameterName.NUMERIC), *string* (models.ParameterName.STRING), *list of strings* (models.ParameterName.STRLIST). *numeric* and *string* inputs have a text field while a *list of strings* has a drop-down menu. Enduser inputs are validated against the type of the input field.

        - **subtype**: Subtypes are used for additional validations: *numeric* fields can be validated for containing  whole and natural numbers.

        - **description**: The label of the input field.

        - **choices**: If the type is *list of strings*, the values of the dropdown menu is provided via *choices*.

        - **ranking**: Ranking sets the ordering of input fields when the fields are displayed.

        - **initial**: The default value of the field.

        - **help_text**: The text displayed when a mouse hovers over the question mark next to the field.



Below are two examples of domain-specific input field types: :ref:`wordcount <wordcount_sc>` and  :ref:`HRMCLite <hrmclite_sc>` smart connector.

- WordCount smart connector input field type

::

      def get_domain_specific_schemas(self):
              schema_data =  [u'Word Count Smart Connector',
                   {
                       u'word_pattern': {'type': models.ParameterName.STRING,
                                        'subtype': 'string',
                                        'description': 'Word Pattern',
                                        'ranking': 0,
                                        'initial': "'[a-z.]+'",
                                        'help_text': 'Regular expression of filtered words'},
                   }
                  ]
              return schema_data


- HRMCLite smart connector input field type

::

        def get_domain_specific_schemas(self):
            schema_data =  [u'HRMCLite Smart Connector',
                 {
                     u'iseed': {'type': models.ParameterName.NUMERIC,
                                'subtype': 'natural',
                                'description': 'Random Number Seed',
                                'ranking': 0,
                                'initial': 42,
                                'help_text': 'Initial seed for random numbers'},
                     u'pottype': {'type': models.ParameterName.NUMERIC,
                                  'subtype': 'natural',
                                  'description': 'Pottype',
                                  'ranking': 10,
                                  'help_text': '',
                                  'initial': 1},
                     u'error_threshold': {'type': models.ParameterName.STRING,
                                          'subtype': 'float',
                                          'description': 'Error Threshold',
                                          'ranking': 23,
                                          'initial': '0.03',
                                          'help_text': 'Delta for iteration convergence'},
                     u'optimisation_scheme': {'type': models.ParameterName.STRLIST,
                                              'subtype': 'choicefield',
                                              'description': 'No. varying parameters',
                                              'ranking': 45,
                                              'choices': '[("MC","Monte Carlo"), ("MCSA", "Monte Carlo with Simulated Annealing")]',
                                              'initial': 'MC', 'help_text': '',
                                              'hidefield': 'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result',
                                              'hidecondition': '== "MCSA"'},
                     u'fanout_per_kept_result': {'type': models.ParameterName.NUMERIC,
                                                'subtype': 'natural',
                                                 'description': 'No. fanout kept per result',
                                                 'initial': 1,
                                                 'ranking': 52,
                                                 'help_text': ''},
                     u'threshold': {'type': models.ParameterName.STRING,
                                    'subtype': 'string',
                                    'description': 'No. results kept per iteration',
                                    'ranking': 60,
                                    'initial': '[1]',
                                    'help_text': 'Number of outputs to keep between iterations. eg. [2] would keep the top 2 results.'},
                     u'max_iteration': {'type': models.ParameterName.NUMERIC,
                                        'subtype': 'whole',
                                        'description': 'Maximum no. iterations',
                                        'ranking': 72,
                                        'initial': 10,
                                        'help_text': 'Computation ends when either convergence or maximum iteration reached'},
                 }
                ]

            return schema_data








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
