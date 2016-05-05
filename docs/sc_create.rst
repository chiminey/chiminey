
.. _create_sc:

Creating a smart connector
-------------------------

Creating a smart connector involves completing three tasks:

  #. providing the core functionality of the smart connector,
  #. attaching resources and optional non-functional properties, and
  #. registering the new smart connector with the Chiminey platform.


Let's create a new smart connector that generates a random number with a timestamp,  and then writes the output to a file.




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


Attaching resources and non-functional properties
"""""""""""""""""""""""""""""""""""""""""""""""""""
Resources and non-functional properties are attached to a smart connector by overriding ``get_ui_schema_namespace`` method of ``chiminey.initialisation.coreinitial.CoreInitial`` class.
New domain-specific variables can be introduced via ``get_domain_specific_schemas`` method. The list
of available resources and non-functional properties is given by ``INPUT_FIELDS`` parameter in ``chiminey/settings_changeme.py``

In this example, we will need to attached a unix compute resource for the computation, and a storage resource for the output location. However, we will not add a non-functional property.
Under chiminey/, we create a python package `randnum`, and add ``initialise.py`` with the following content::

    from chiminey.initialisation import CoreInitial from django.conf import settings
    class RandNumInitial(CoreInitial):
    def get_ui_schema_namespace(self):
            schemas = [
                    settings.INPUT_FIELDS[’unix’],
                    settings.INPUT_FIELDS[’output_location’],
    ] return schemas
    # ---EOF ---





:ref:`Various examples <examples>` are given to show how a smart connector is created.

..
  These examples also explain
  how  features, such as  data curation and parameter sweep,
  can be included within a smart connector definition.
