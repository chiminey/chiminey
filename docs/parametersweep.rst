
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

The set of parameters are defined at job submission time,
rather than being "hard-coded" to the definition of the smart connector.
This is done using `templating language <https://docs.djangoproject.com/en/dev/ref/templates/api/>`__.
Here are the steps
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
values for the selected set of parameters during a smart connector definition. The actual values of the parameters
can be
    - hardcoded during the smart connector definition or

    - collected from the enduser input during job submission.

A smart connector job that is composed of multiple tasks, due to an  internal parameter sweep,  is considered to be complete when
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


Imapct of unknown parameters in a sweep map
'''''''''''''''''''''''''''''''''''''''''''

Including an unknown parameter
to a sweep map increases the generated number of tasks/jobs, provided that
the number of the values of the unknown parameter is more than 1.

Suppose ``var1`` and ``var2`` are known parameters to  a specific
smart connector, and these parameters are used as part of an external sweep.
If the end-user mistakenly provided a sweep map ``{"var1": [7,9], "var2": [42], "x": [1,2]}``,
four jobs, instead of two jobs, will be created.

The additional jobs
waste computing and storage resources. However, there are cases where such  feature is useful.
The end-user can use this feature to run identical jobs, and then check
whether the jobs produce the same output.


.. [*] The total number of tasks that are generated per job depends on the type of the smart connector. In addition to the sweep map, domain-specific variables or constraints  play a role in determining the number of tasks  per job.


.. seealso::

        :ref:`Quick Example: The Unix Random Number Smart Connector <quick_example>`
           

        :ref:`The Internal Sweep Random Number Smart Connector <internal_sweep_randnum>`








