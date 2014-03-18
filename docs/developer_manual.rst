
================
Developer Manual
================

.. _smart_connector_desc:
Smart Connector
---------------

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


Here, we use the following examples to show the different features of a smart connector
and how a smart connector is defined and registered within a Chiminey server.

.. toctree::
    quick_example

