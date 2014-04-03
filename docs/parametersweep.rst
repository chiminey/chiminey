
.. _parametersweep:


Parameter Sweep
~~~~~~~~~~~~~~~

The Chiminey platform provides two types of parameter sweeps:

    - :ref:`External parameter sweep <external_parameter_sweep>`

    - :ref:`Internal parameter sweep <internal_parameter_sweep>`


.. _external_parameter_sweep:

External Parameter Sweep
""""""""""""""""""""""""

**External parameter sweep** allows end-users to simultaneously submit and run multiple jobs.
The external  sweep gives power to the end-users to provide a range of input values
for a set of parameters of their choice,
and the resulting set of jobs span all possible values from that parameter space.

The set of parameters are defined as part of input data preparation,
rather than being "hard-coded" to the definition of the smart connector.
This is done using `templating language <https://docs.djangoproject.com/en/dev/ref/templates/api/>`__.
Here are the steps:
    #. Identify the input files that contain the parameters of your choice.

    #. Surround each parameter name with double curly brackets. Suppose an input file entry is ``var1 15``. Replace this line by ``{{var1}} 15``; where ``15`` is the default value.

    #. Save each input file as ``filename_template``.

The end-user provides the range of values of these parameters via a :ref:`sweep map <sweep_map>` during job submission.

The common usecases for the external parameter sweep  are to generate multiple results across one or more variation ranges
for later comparison, and to quickly perform experimental or ad-hoc variations on existing smart connectors.



.. _internal_parameter_sweep:

Internal Parameter Sweep
""""""""""""""""""""""""

**Internal parameter sweep** allows developers to create
a smart connector that spawns  multiple independent tasks
during the smart connector's job execution.
When a smart connector is created, the developer includes a set of parameters
that will  determine the number of tasks  spawned during the execution
of the smart connector.

The developer uses a :ref:`sweep map <sweep_map>` to specify a range of
values for the selected set of parameters during a smart connector definition. This is done by
subclassing  ``Parent``, which is located at ``chiminey/corestages/parent.py``, and
overwriting the method ``get_internal_sweep_map(self, ...)`` to include the new sweep map.
The default sweep map generates one task.

::

    def get_internal_sweep_map(self, settings, **kwargs):
        rand_index = 42
        map = {'val': [1]}
        return map, rand_index


**NB**: A smart connector job that is composed of multiple tasks, due to an  internal parameter sweep,  is considered to be complete when
each task  either  finishes successfully or fails beyond recovery.


.. _sweep_map:

Sweep Map
"""""""""

A **sweep map** is a `JSON dictionary <http://www.json.org/>`__  that is used to specify a range of values for a set of parameters.
    - The key of the dictionary corresponds to a parameter name.

    - The value of the dictionary is a list of possible values for that parameter.


Below is an example of a sweep map.

::

    sweep_map = {"var1": [7,9], "var2": [42]}


The cross-product of the values of the parameters in a sweep map is used to determine the minimum [*]_
number of tasks or jobs generated during job submission.  The above sweep map, for example, generates
    - **two jobs** if used for external parameter sweep, or

    - **two tasks** per job if used for internal parameter sweep


.. _unknown_param:

Imapct of unknown parameters in a sweep map
'''''''''''''''''''''''''''''''''''''''''''

An **unknown parameter** is a parameter that is not needed during the execution of a smart
connector. A **known parameter**, on the other hand, is a parameter whose value is needed
for the correct functioning of a smart connector.


Including an unknown parameter in a sweep map does not have
any ill-effect during execution. However,
this parameter causes an increase in the number of generated
tasks/jobs, provided that
the number of the values of the unknown parameter is more than one.


Suppose ``var1`` and ``var2`` are known parameters, and ``x`` is an unknown parameter of a specific
smart connector; and  the sweep map is ``{"var1": [7,9], "var2": [42], "x": [1,2]}``.

    - If the sweep map is used for external parameter sweep, the number of jobs doubles due to the
      inclusion of parameter ``x`` with two values. If the sweep map is used for internal sweep, the number of tasks
      doubles as well. If the value of ``x`` is changed to ``[1,2,3]``, the number of jobs/tasks
      triples, and so on.

The additional jobs or tasks waste computing, storage and network resources.  However,
there are cases where such feature is useful.
    - The end-user can use this feature to run  jobs with identical inputs, and then compare
      whether the jobs produce the same output.

    - If each task has unpredictable output irrespective of other variables being constant,
      the developer can use the feature to run many of these tasks per job, each task with different output.
      For example, generating a random number without fixing the seed almost always guarantees a new number.



.. [*] The total number of tasks that are generated per job depends on the type of the smart connector. In addition to the sweep map, domain-specific variables or constraints  play a role in determining the number of tasks  per job.


.. seealso::

        External sweep parameter:
            - :ref:`Quick Example: The Unix Random Number Smart Connector <quick_example>`

        Internal sweep parameter:
            - :ref:`The Internal Sweep Random Number Smart Connector <internal_sweep_randnum>`








