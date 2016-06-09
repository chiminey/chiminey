

.. _hrmc_sc:

The Hybrid Reverse Monte Carlo (HRMC) Smart Connector
========================================



..
  note:: This documentation is under construction


.. note:: This example is significantly more complicated than the previous examples. Therefore we describe here the unique features of this connector and invite the reader to read the source code for this connector in detail. It combines a number of features from the previous examples and uses the same overall architecture.


The Hybrid Reverse Monte Carlo Smart Connector, hereafter HRMC SC, is designed to run :ref:`the implementation of
an HRMC simulation by  George Opletal <hrmc-source-code>`. The HRMC SC runs HRMC simulations on a cloud compute resource.
It reads inputs from a remote file system, and then writes output to a remote file system *and* a data curation service, i.e. MyTardis.
The HRMC SC enables  end-users to control the degree of the provided fault tolerance support. Furthermore, this smart connector includes
a sweep functionality to enable end-users to simultaneously execute multiple HRMC jobs from a single submission.

The HRMC SC and related topics will be discussed as follows:

- :ref:`HRMC source code<hrmc-source-code>`

- :ref:`The Core function<hrmc-core-function>`

- :ref:`Attaching resources and non-functional properties<hrmc-ataching_resources>`

- :ref:`Registering the HRMC SC<hrmc_registration>`








.. _hrmc-source-code:

Hybrid Reverse Monte Carlo - Source Code Version 2.0 (Oct 2012)
----------------------------------------------------------

| Code development by:
| Dr. George Opletal
| g.opletal@gmail.com
| Applied Physics RMIT, Melbourne Australia.

| Contributions to code development:
| Dr. Brendan O'Malley
| Dr. Tim Petersen

Published in:

  G. Opletal, T. C. Petersen, I. K. Snook, S. P. Russo, HRMC_2.0: Hybrid Reverse Monte Carlo method with silicon, carbon and germanium potentials, Com. Phys. Comm., 184(8), 1946-1957 (2013).

License: CPC License: http://cpc.cs.qub.ac.uk/licence/licence.html



.. _hrmc-core-function:

HRMC Core Function
----------------------------------------------------------
The core functionality of the HRMC SC is provided through a :ref:`payload<payload>`. The HRMC payload is similar to the following.

::

    payload_hrmc/
    |--- bootstrap.sh
    |--- process_payload
    │    |--- HRMC2.tar.gz
    |    |--- PSDCOde.tar.gz
    │    |--- schedule.sh
    │    |--- main.sh


The HRMC SC requires packages like dos2unix, fortran compiler. Thus, all the required dependancies are specified in  ``bootstrap.sh``.
The content of  ``bootstrap.sh`` is as follows:

::

   #!/bin/bash

    yum -y install dos2unix gcc-gfortran compat-libgfortran-41 gcc-gfortran.x86_64


The payload includes domain-specific executables, i.e. ``HRMC2.tar.gz`` and ``PSDCOde.tar.gz``.
The ``schedule.sh``  of HRMC SC contains process-specific configurations. ``schedule.sh`` is responsible to extract
the executables for each HRMC process. Below shows the content of ``schedule.sh``.


::


    #!/bin/bash
    # version 2.0

    INPUT_DIR=$1
    OUTPUT_DIR=$2

    tar --extract --gunzip --verbose --file=HRMC2.tar.gz
    f95 HRMC2/hrmc.f90 -fno-align-commons -o HRMC

    tar --extract --gunzip --verbose --file=PSDCode.tar.gz
    gfortran PSDCode/PSD.f -o PSDCode/PSD



``main.sh`` is the core of HRMC SC.

::

    #!/bin/bash
    # version 2.0

    INPUT_DIR=$1
    OUTPUT_DIR=$2

    cp HRMC $INPUT_DIR/HRMC
    cd $INPUT_DIR
    ./HRMC >& ../$OUTPUT_DIR/hrmc_output
    cp input_bo.dat ../$OUTPUT_DIR/input_bo.dat
    cp input_gr.dat ../$OUTPUT_DIR/input_gr.dat
    cp input_sq.dat ../$OUTPUT_DIR/input_sq.dat
    cp xyz_final.xyz  ../$OUTPUT_DIR/xyz_final.xyz
    cp HRMC.inp_template ../$OUTPUT_DIR/HRMC.inp_template
    cp  data_errors.dat   ../$OUTPUT_DIR/data_errors.dat

    cp -f xyz_final.xyz ../PSDCode/xyz_final.xyz
    cd ../PSDCode; ./PSD >&  ../$OUTPUT_DIR/psd_output
    cp PSD_exp.dat ../$OUTPUT_DIR/
    cp psd.dat ../$OUTPUT_DIR/











.. _hrmc-ataching_resources:

Attaching Resources and Non-functional properties
----------------------------------------------------------


.. _hrmc_registration:

Registering the HRMC SC
----------------------------------------------------------




Setup
`````

As with the previous examples, we setup the new connector payload::

    mkdir -p /var/chiminey/remotesys/my_payloads
    cp -r  /opt/chiminey/current/chiminey/examples/hrmc2/payload_hrmc /var/chiminey/remotesys/my_payloads/


Then register the new connector within chiminey::

    sudo su bdphpc
    cd /opt/chiminey/current
    bin/django hrmc
    Yes

This example is significantly more complicated than the previous random number examples. Therefore we describe here the  unique features of this connector and invite the reader to read the source code for this connector in detail. It combines a number of features from the previous examples and uses the same overall architecture.

The Input Directory
```````````````````

As described earlier, each connector in Chiminey system can elect to specify a *payload* directory that is loaded to each VM for cloud execution.  This payload is fixed for each type of connector.

However, if practice you would likely want to vary the behaviour of *different* runs of the same connector, to change the way a process is executed or perform exploratory analysis.

This is accomplished in Chiminey by the use of a special *input directory*.  This is one of the most powerful features of a smart connector as it allows individual runs to be fully parameterised on the initial input environment and environment during execution.

Ideally the payload directory would contains source or code for the application, and the input directory would contain configuration or input files to that application.

The input directory is a remote filesystem location (like the output directory) defined and populated before execution, which contains files that will be loaded into the remote copy of the payload after it has been transferred to the cloud node, *for every run*. Furthermore the contents of input files in that directory can be varied at run time.

Any files within the input directory can be made into a template by adding the suffix ``_template`` to the filename.  Then, this file is interpreted by the system as a Django template file.

Consider the application ``foo` has its source code in a payload, but requires a ``foo.inp``file containing configuraiton information.  For example::

     # foo input file
     iseed 10
     range1 45
     range2 54
     fudgefactor 12

is an example input for one run.  To parameterise this file you rename it to ``foo.inp_template`` and replace the values that need to vary with equivalent template tags::

    # foo input file
    iseed {{iseed}}
    range1 {{range1}}
    range2 {{range2}}
    fudgefactor 12

The actual values to be used are substituted at runtime by the system.
THe values can come from the external sweep map, the internal sweep map, domain-specific values in the submission page, and constant values set within the input directory.

For example, the ``iseed`` value may be an input field  on the submission page, the ``range1`` value may be predefined to be constant during all runs, and the ``range2`` has to go between the values ``50--52``.

This parameterisation is performed using a ``values`` file,  which is a special file at the top of the input directory. This JSON dictionary contains values to be instantiated into template files at run time.  The values files included in the original input directory can contain constant values that would then apply generally to any connector using that input directory.

For this example, we the directory would include a file ``values`` containing::

    {
        "range1": 45
    }

Then initially, all runs of ``foo`` will include::

  range1 45

in the ``foo.inp`` file

However, Chiminey also automatically populates the values directory with other key/value s representing the data typed into the job submission page  form fields, the specific values from  the sweep map for *that* run.  All these values can be used in instantiation of the template files.

For this example, if at jobs submission time the user entered ``iseed`` as 10, and the sweep map values as ``{"range2": [50, 51]}`` then external sweep will produce multiple processes each with a values file across the range ``range2``.  For example::

   {
       "iseed": 10
       "range1": 45,
       "range2": 50,

   }

or::

   {
       "iseed": 10
       "range1": 45,
       "range2": 51,
   }


The ``foo.inp_template`` file is matched against the appropriate ``values`` file, to create the required input file.  For example::

    # foo input file
    iseed 10
    range1 45
    range2 50
    fudgefactor 12

or::


    # foo input file
    iseed 10
    range1 45
    range2 51
    fudgefactor 12

Hence these are are the ``foo.inp`` files for each run.

The use case for such a connector:

#. Prepare a payload containing all source code and instructions to compile as before.

#. Prepare a remote input directory containing all the input files needed by the computation.  If the contents of any of these files need to vary, then rename the files and add ``{{name}}`` directives to identify the points of variation. Names are:

    #.  keys from the input schemas within the submission page.
    #.  constant values for the whole computation.

#. Optionally add a ``./values`` file containing a JSON dictionary of mappings between variables and values.  These entries are constant values for the whole computation.

#. During execution, Chiminey will load up values files and propagate them in input and output directories, will put values corresponding to all input values, individual values from the space of sweep variables.  These variables will be substituted into the template to make an original input file suitable for the actual execution.

In the HRMC connector, the ``HRMC.inp`` file is templated to allows substitution of values from both the job submission page and from the sweep variable.  See ``input_hrmc/initial`` directory and the inluded ``HRMC.inp_template`` and ``values`` files.

Complex Internal Sweeps
```````````````````````

The ``randnuminternalsweep`` connector defined a simple map in the parent stage that maps an input into two variations based on a variable ``var``.  While that value was not used in that example, we can see that if a input directory was used then each of the two variations would get different values for the ``var`` variable in the ``values`` file and could be used in any input template file.

For the HRMC smart connector, the mapping is significantly more complicated.  In the
``get_internal_sweep_map`` method of ``hrmcparent.py``, the map is definedin stages using existing variables (in the ``values`` file), the values in the original form, plus new variables based on random numbers and on the current iteration of the calculation.    Thus the number of processes and their starting variables can be specialised and context sensitive and then instantiated into template files for execution.


Use of Iterations
`````````````````

In the random numbers the standard behaviour was to execute stages sequentially from ``Configure`` through to ``Teardown``.  However, in the HRMC example, we support an run_setting variable ``system/id`` which allows a set of stages to be repeated multiple times and two new core stages, ``Transform`` and ``Converge``.  These stages are specialised in the HRMC example:

-  After the results are generated during the execution phase, the ``HRMCTransform`` stages calculates a criterion value (the ``compute_psd_criterion`` method). The execution results are then prepared to become input for a next iteration (the ``process_outputs`` method)

-  In the ``HRMCConverge`` stage, the new criterion value is then compared a previous iterations' value and if the difference is less than a threshold, then the smart connector execution is stopped.  Otherwise, the value ``system/id`` is incremented and the triggering state for the execution phase is created which causes these stages to be re-executed.  Finally, to handle the situation where the criterion will diverges or is converging too slowly, the ``HRMCConverge`` stage also halts the computation is the ``system/id`` variable exceeds a fixed number of iterations.

See the ``hrmctransform.py`` and ``hrmcconverge.py`` modules for more details.


Complex Mytardis Interactions
`````````````````````````````

The HRMC example, expands on the MyTardis experiment created in the randonnumber example.

As before the ``HRMCConverage`` defines a curate_data method, and the ``HRMCTransform`` and ``HRMCConverge`` define a ``curate_dataset`` method.  However, the later methods are significantly more complicated than the previous example.

The ``mytardis/create_datadata`` method takes a function for the dataset_name as before, which has a more complicated implementation.  However, this example also uses the ``dfile_extract_func`` argument which is a dict from datafile names to functions.
For all contained datafiles within the dataset, their names are matched to this dictionary, and when found, the associated function is executed with a file pointer to that files *contents*.  The function then results the graph metadata required.

For example,
``HRMCTransform`` includes as an argument for ``mytardis.create_dataset``::

    dfile_extract_func= {'psd.dat': extract_psd_func,
    'PSD_exp.dat': extract_psdexp_func,
    'data_grfinal.dat': extract_grfinal_func,
    'input_gr.dat': extract_inputgr_func}

Here for any datafile in the new dataset named `psd.dat` chiminey will run::

    def extract_psd_func(fp):
        res = []
        xs = []
        ys = []
        for i, line in enumerate(fp):
            columns = line.split()
            xs.append(float(columns[0]))
            ys.append(float(columns[1]))
        res = {"hrmcdfile/r1": xs, "hrmcdfile/g1": ys}
        return res

Here the function returns a directionry containing mappings to two lists of floats extracted from the datafile ``psd.dat``.  This value is then added as a metadata field attached to that datafile.  For example::

    graph_info   {}
    name         hrmcdfile
    value_dict   {"hrmcdfile/r1": [10000.0, 20000.0, 30000.0, 40000.0, 50000.0, 60000.0, 70000.0, 80000.0, 90000.0, 100000.0, 10000.0, 20000.0], "hrmcdfile/g1": [21.399999999999999, 24.27, 27.27, 25.649999999999999, 22.91, 20.48, 18.649999999999999, 17.16, 16.34, 16.219999999999999, 15.91, 15.460000000000001]}
    value_keys   []

This can then be data to be used by the dataset level graph ``hrmcdset`` described in the ``dataset_paramset`` argument of the ``create_dataset`` method.




.. cp -r  /opt/chiminey/current/payload_hrmc /var/chiminey/remotesys/my_payloads/
.. cp /opt/chiminey/current/chiminey/randomnums.txt /var/chiminey/remotesys/
