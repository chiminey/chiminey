Parameters of any smart connector fall into either of the following
input form field types: \* `Computation
platform <#computation_platform>`__ \* `Cloud
resource <#cloud_resource>`__ \* `Location <#location>`__ \*
`Reliability <#reliability>`__ \* `MyTardis <#mytardis>`__ \* `Parameter
Sweep <#sweep>`__ \* `Domain-specific <#domain_specific>`__

 ###Computation platform The names of previously registered computation
platforms (see `Registering Computation
Platforms </chiminey/chiminey/wiki/Enduser-Manual#wiki-register_computation_resource>`__)
are populated into a drop down menu, labeled as *Computation Platform
Name*. The enduser selects the platform name that represent the
computation platform for the current job.

 ### Cloud resource Cloud resource parameters enable the enduser to
specify the *maximum* and the *minimum* number of virtual machines (VMs)
that the Chiminey server can create for the current job. The *maximum
number* is used to bound the number of VMs created for the current job
while the *minimum number* is used to specify the smallest number of VMs
that are needed for the job. The Chiminey server will terminate the job
if the number of VMs that are created by the server is less than the
*minimum number* requirement. The default values of both parameters is
1.

 ### Location A *location* is a storage platform path to/from which
files are transferred. There are *input* and *output* locations:

1. *Input location* is a storage platform path from which the input
   files of the current job are retrieved.
2. *Output location* is a storage platform path to which the results of
   the current job are transferred.

Location parameters are used to specify the input location and the
output location of the current job. A location is generally represented
as ``storage_platform_name/offset``: *storage\_platform\_name*
represents the name of a previously registered storage platform, and
*offset* represents the location of the files relative to the root path
of the platform (see `Registering Storage
Platform </chiminey/chiminey/wiki/Enduser-Manual#wiki-registering-storage-platform>`__
for details about storage platform, in particular platform name and root
path).

For instance, a unix-based storage platform is registered with platform
name ``unix_home`` and root path ``/home/enduser``.

1. If the input location is ``unix_home/hrmc``, then the input files are
   located at ``unix_home`` platform under ``/home/enduser/hrmc``
   directory.

2. If the input location is ``unix_home``, then the input files are
   located at ``unix_home`` platform under ``/home/enduser`` directory.

 ### Reliability

Fault tolerance support is provided to each job. However, the enduser
can limit the degree of such support using the reliability parameters:
*reschedule failed processes* and *maximum retries*:

1. Reschedule failed processes: The Chiminey server reschedule failed
   processes. However, the enduser can choose to prevent the
   rescheduling of failed processes. In cases where a job is composed of
   a many processes, failure of some processes here and there may not
   have a significant impact on the overall outcome of the job. On such
   scenarios, the enduser may ignore failed processes. By doing this,
   the job completes relatively quickly as no time is spent on executing
   recovery measures, rescheduling the failed process, and waiting for
   the failed process to complete.

2. Maximum retries: The maximum number of times attempts to recover a
   failed process before the process is flagged as failed beyond
   recovery.

 ### MyTardis The Chiminey server uses
`MyTardis <https://github.com/mytardis/mytardis/>`__ to curate the
output of a given job. The MyTardis parameters are therfore used to

1. opt in to curation services, and
2. specify the MyTardis instance to which the output of the job is sent
   for curation. The names of previously registered MyTardis-based
   storage platforms (see `Registering Storage Platforms,
   MyTardis </chiminey/chiminey/wiki/Enduser-Manual#wiki-mytardis_storage_platform>`__)
   are populated into a drop down menu, labeled as *MyTardis Platform*.

 ### Parameter Sweep

Sweep allows end-users to simultaneously submit and run multiple jobs.
The sweep gives power to the end-users to provide range of input values
for parameters of their choice, and the resulting set of jobs span all
possible values from that parameter space. These ranges of parameters
are defined at job submission time, rather than being "hard-coded" to
the definition of the smart connector. The common usecases for this
feature are to generate multiple results across one or more variation
ranges for later comparison, and to quickly perform experimental or
ad-hoc variations on existing connectors.

Endusers specify the parameter(s) and their possible values through the
sweep parameter.

 ### Domain-specific

Domain-specific parameters are needed to guide the execution of the core
functionality of a specific smart connector. Unlike the parameters
above, these parameters are unlikely to be shared among smart
connectors. For example, the reliability parameter *maximum retries* is
needed in all smart connectors to which reliability is incorporated;
however, the domain-specific parameter *pottype* is needed in HRMC smart
connector but not in the other existing smart connectors.
