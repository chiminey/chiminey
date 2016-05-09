
.. _create_sc:

Creating a smart connector
-------------------------

Creating a smart connector involves completing three tasks:

  #. providing :ref:`the core functionality <sc_core_fcn>`` of the smart connector,
  #. attaching :ref:`resources and optional non-functional properties <sc_attach_resources>``, and
  #. :ref:`registering <sc_registration>` the new smart connector with the Chiminey platform.


Each tasks are discussed below by  creating an example smart connector. This  smart connector  generates a random number with a timestamp,  and then writes the output to a file.

.. include:: <loginterm.rst>



.. _sc_core_fcn:

The Core Function
""""""""""""""""

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
"""""""""""""""""""""""""""""""""""""""""""""""""""
Resources and non-functional properties are attached to a smart connector by overriding ``get_ui_schema_namespace`` method of ``chiminey.initialisation.coreinitial.CoreInitial`` class.
New domain-specific variables can be introduced via ``get_domain_specific_schemas`` method.  In this example, we will need to attached a unix compute resource for the computation, and
a storage resource for the output location. However, we will not add a non-functional property.

Under chiminey/, we create a python package `randnum`, and add ``initialise.py`` with the following content::

    from chiminey.initialisation import CoreInitial from django.conf import settings
    class RandNumInitial(CoreInitial):
    def get_ui_schema_namespace(self):
            schemas = [
                    settings.INPUT_FIELDS[’unix’],
                    settings.INPUT_FIELDS[’output_location’],
    ] return schemas
    # ---EOF ---



.. _sc_registration:

Registration
"""""""""""""""

The final step is registering the smart connector  with the Chiminey platform. The details of this smart connector
 will be added to the dictionary ``SMART CONNECTORS`` in ``chiminey/settings changeme.py``.
  The details include a unique name (with no spaces), a python path to ``RandNumInitial`` class,
   the description of the smart connector, and the absolute path to the payload.

"randnum": {
           "name": "randnum",
           "init": "chiminey.randnum.initialise.RandNumInitial",
           "description": "Randnum generator, with timestamp",
           "payload": "/opt/chiminey/current/payload_randnum"
},

Finally, restart the Chiminey platform and then activate ``randnum`` smart connector. You need to exit the docker container and execute the following::

  $ sh restart
  $ ./activatesc randnum


The list
    of available resources and non-functional properties is given by ``INPUT_FIELDS`` parameter in ``chiminey/settings_changeme.py``



:ref:`Various examples <examples>` are given to show how a smart connector is created.

..
  These examples also explain
  how  features, such as  data curation and parameter sweep,
  can be included within a smart connector definition.
