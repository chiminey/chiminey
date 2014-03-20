API Reference
=============

Chiminey Stage APIs
-------------------

:mod:`~chiminey.mytardis`  -- MyTardis APIS
'''''''''''''''''''''''''''''''''''''''''''

The MyTardis module provides functions that allow publishing Chiminey results to a connected MyTardis System, allowing the online storing, access and sharing capabilities of data and metadata.


Datastructures
;;;;;;;;;;;;;;

paramset


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.. automodule:: chiminey.mytardis
   :members:


.. autofunction:: chiminey.mytardis.create_experiment

.. autofunction:: chiminey.mytardis.create_dataset


Example::

 def _get_exp_name_for_make(settings, url, path):
                    return str(os.sep.join(path.split(os.sep)[-2:-1]))

                def _get_dataset_name_for_make(settings, url, path):
                    return str(os.sep.join(path.split(os.sep)[-1:]))

                self.experiment_id = mytardis.create_dataset(
                    settings=mytardis_settings,
                    source_url=encoded_d_url,
                    exp_id=self.experiment_id,
                    exp_name=_get_exp_name_for_make,
                    dataset_name=_get_dataset_name_for_make,
                    experiment_paramset=[],
                    dataset_paramset=[
                        mytardis.create_paramset("remotemake/output", [])]
                    )



.. autofunction:: chiminey.mytardis.retrieve_datafile

.. autofunction:: chiminey.mytardis.create_graph_paramset

.. autofunction:: chiminey.mytardis.create_paramset


:mod:`~chiminey.storage` -- Storage APIS
''''''''''''''''''''''''''''''''''''''''


This package provides a file-like api for manipulating local and remote files and functions at locations specified by platform instances.


Datastructures
;;;;;;;;;;;;;;


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.. automodule:: chiminey.storage
   :members:
   :undoc-members:


:mod:`~chiminey.sshconnection` -- Manipulation of Remote Resources
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Datastructures
;;;;;;;;;;;;;;

ssh_client

Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


.. autofunction:: chiminey.sshconnection.open_connection

:mod:`~chiminey.compute` -- Execution Of Remote Commands
''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Using an open ssh_client connector from sshconnector, these commands execute commands remotely on the target server.

Datastructures
;;;;;;;;;;;;;;


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


.. autofunction:: chiminey.compute.run_command_with_status

.. autofunction:: chiminey.compute.run_command_with_tty

.. autofunction:: chiminey.compute.run_make

.. autofunction:: chiminey.compute.run_command



:mod:`~chiminey.messages` -- Logging communication for Chiminey
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

This package, modelled off the django logging module, posts status messages for the BDP system.  There are two classes of context for the user of this API:

1.  Within stage implementation, messages will be displayed within the status field in the job list UI. 

2. During job submission, messages will be displayed on the redirected page as a header banner.


Messages are processed by a separate high-priority queue in the celery configuration.  Note that message delivery may be delayed due to celery priority or db exclusion on the appropriate context, so this function should not be used for real-time or urgent messages.  

Datastructures
;;;;;;;;;;;;;;

By convention, error messages are final messages in job execution to indicate fatal error (though job might be restarted via admin tool) and success is used to describe final successful execution of the job.


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

Send a msg at the required priority level, as per the django logging module.  

Uses contextid  field of settings to determine which running context to assign 	messages. 


.. autofunction:: chiminey.messages.debug

.. autofunction:: chiminey.messages.error

.. autofunction:: chiminey.messages.info

.. autofunction:: chiminey.messages.warn

.. autofunction:: chiminey.messages.success

:mod:`~chiminey.run_settings` -- Contextual Namespace for Chiminey
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The current state of any BDP calculation is represented as a context model instance, with an associated run_settings instance.  This run_setting serves as input, output and scratch symbol table for all job execution.  

The contextual namespace is used for numerous purposes in the BDP, including:

* Input parameters for Directive submission UI dialog
* Single source of truth for building settings dicts for BDP API modules.
* Job execution state
* Diagnostics and visualisation of job progress
* Stage triggering and scheduling during directive execution

Conceptually run_settings is a set of parameter sets each of which is  conformant to a predefined schemas, that are defined in the admin tool.

run_settings is a two-level dictionary, internally serialised to models as needed.


Datastructures
;;;;;;;;;;;;;;

context

A two level dictionary made up of schema keys and values. Conceptually, this structure is equivalent to a two-level python dictionary, but should be accessed via the API below.  For example,

{ http://acme.edu.au/schemas/stages : { “key”: id, “id”: 3}  }

Keys are concatenation of schema namespace and name, for example:
http://acme.edu.au/schemas/stages/key 


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

.. autofunction:: chiminey.runsettings.getval

.. autofunction:: chiminey.runsettings.setval
	


:mod:`~chiminey.cloudconnection` -- Cloud Connection
''''''''''''''''''''''''''''''''''''''''''''''''''''

Datastructures
;;;;;;;;;;;;;;


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


:mod:`~chiminey.corestages` -- Processing Steps in a directive
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

This is an abstract class that forms the interface for all directives, both smart connectors and utilties to provides steps in a calcuation.

Datastructures
;;;;;;;;;;;;;;


.. autoclass:: chiminey.corestages.stage.Stage
   :members: isValid, is_triggered, process, output


Module Functions and Constants
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;




:mod:`~chiminey.simpleui` -- UI view members
--------------------------------------------

.. automodule:: chiminey.simpleui.views
   :members:
   :undoc-members:




