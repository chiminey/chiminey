An end-user submits a smart connector job, monitors the job, visualises
job results and publishes the result to the public BDP index. In this
documentation, following topics are covered: \* `Getting Chiminey
Account <#getting_chiminey_account>`__ \* `Login <#login>`__ \*
`Logout <#logout>`__ \* `Configuring platform
settings <#configure_platform>`__ \* `Submitting a
job <#submitting_job>`__ \* `Monitoring a job <#monitoring_job>`__ \*
`Terminating a job <#terminating_job>`__ \* `Managing
presets <#managing_presets>`__

 ### Getting Chiminey Account

Chiminey accounts are managed by admin users. Therefore, in order to get
access to a specific Chiminey server, the end-user should contact the
admin of the Chiminey server.

 ### Login

End-users login via the web interface of the Chiminey server

1. click 'login' on the home page
2. enter Chiminey credentials
3. click 'Login'

.. figure:: images/login.png
   :alt: Login page

   Login Page
 ### Logout

1. click 'Logout

.. figure:: images/logout.png
   :alt: Logout

   Logout Page
 ### Platform Settings Configuration

A Chiminey server supports two types of platforms: computation and
storage. A computation platform is where the core functionality of a
smart connector is executed while a storage platform is the destination
of the smart connector output. Prior to submitting a job, end-users need
to register at least one computation and one storage platforms. In this
section, following topics are covered:

-  `Registering Computation Platform <#register_computation_platform>`__
-  `Registering Storage Platform <#register_storage_platform>`__
-  `Updating Computation/Storage Platform <#update_platform>`__
-  `Deleting Computation/Storage Platform <#delete_platform>`__

 #### Registering Computation Platform

Two types of computation platforms can be registered within the Chiminey
UI. The types are `Cloud <#cloud_platform>`__ and
`Cluster/Unix <#cluster_unix_platform>`__.

 ##### Cloud Computation Platform

    1.  Navigate to the Chiminey server homepage
    2.  Log in with credentials
    3.  Click 'Settings'
    4.  Click 'Computation Platform' from the 'Settings' menu
    5.  Click 'Add Computation Platform'
    6.  Click the *Cloud* tab.
    7.  Select the platform type from the drop down menu. You may have
        access to more than one type of cloud service, e.g., NeCTAR and
        Amazon.
    8.  Enter a unique platform name. This name should be something you
        could remember.
    9.  Enter credentials such as EC2 access key and EC2 secret key
    10. You can optionally enter the VM image size
    11. Click 'Add'. The newly added cloud-based computation platform
        will be displayed.

Fig. Adding cloud-based computation platform |Adding cloud-based
computation platform|

 ##### Cluster/Unix

    1.  Navigate to the Chiminey server homepage
    2.  Log in with credentials
    3.  Click 'Settings'
    4.  Click 'Computation Platform' from the 'Settings' menu
    5.  Click 'Add Computation Platform'
    6.  Click the *Cluster/Unix* tab.
    7.  Enter a unique platform name. This name should be something you
        could remember.
    8.  Enter IP address or hostname of the cluster head node or any
        Unix server
    9.  Enter credentials, i.e. username and password. Password is not
        stored in the Chiminey server. It is temporarily kept in memory
        to establish a private/public key authentication from the
        Chiminey server to the computation platform.
    10. Enter homepath. This is the location where .ssh directory
        resides. The home path is needed to store a public key on the
        cluster head node or the unix server.
    11. Enter rootpath. The root path is used as the working directory
        during execution.
    12. Click 'Add'
    13. The newly added computation platform will be displayed under
        Cluster/Unix list.

Fig. Adding cluster/unix-based computation platform |Adding
cluster/unix-based computation platform|

 #### Registering Storage Platform Two types of storage platforms can be
registered within the Chiminey UI. The types are
`Unix <#unix_storage_platform>`__ and
`MyTardis <#mytardis_storage_platform>`__.

 ##### Unix

    1.  Navigate to the Chiminey server homepage
    2.  Log in with credentials
    3.  Click ‘Settings’
    4.  Click ‘Storage Platform’ from the ‘Settings’ menu
    5.  Click ‘Add Storage Platform’
    6.  Click the *Unix* tab.
    7.  Enter a unique platform name. This name should be something you
        could remember.
    8.  Enter IP address or hostname of the unix-based storage
    9.  Enter credentials, i.e. username and password. Password is not
        stored in the Chiminey server. It is temporarily kept in memory
        to to establish a private/public key authentication from the
        Chiminey server to the storage.
    10. Enter homepath. This is the location where .ssh directory
        resides. The home path is needed to store a public key on the
        unix server.
    11. Enter rootpath. The root path is used as the working directory
        of the Chiminey server.
    12. Click ‘Add’
    13. The newly added storage platform will be displayed under ‘Unix’
        list.

Fig. Adding unix-based storage platform |Adding unix-based storage
platform|

 ##### MyTardis

    1.  Navigate to the Chiminey server homepage
    2.  Log in with credentials
    3.  Click ‘Settings’
    4.  Click ‘Storage Platform’ from the ‘Settings’ menu
    5.  Click ‘Add Storage Platform’
    6.  Click the *MyTardis* tab.
    7.  Enter a unique platform name. This name should be something you
        could remember.
    8.  Enter IP address or hostname of the MyTardis instance
    9.  Enter credentials, i.e. username and password. Username and
        password are stored on the Chiminey server.
    10. Click ‘Add’
    11. The newly added storage platform will be displayed under
        MyTardis list.

Fig. Adding MyTardis-based storage platform |Adding MyTardis-based
storage platform|

 #### Updating Computation/Storage Platform

    1. Navigate to the Chiminey server homepage
    2. Log in with credentials
    3. Click ‘Settings’
    4. To update a computation platform, click ‘Computation Platform’
       whereas to update a storage platform, click ‘Storage Platform’
       from the ‘Settings’ menu.
    5. Locate the platform you wish to update, then click ‘Update’
    6. Make the changes, and when finished click ‘Update’

Fig. Updating a platform |Updating a platform|

 #### Deleting Computation/Storage Platform

    1. Navigate to the the Chiminey server homepage
    2. Log in with credentials
    3. Click ‘Settings’
    4. To delete a computation platform, click ‘Computation Platform’
       whereas to delete a storage platform, click ‘Storage Platform’
       from the ‘Settings’ menu.
    5. Locate the platform you wish to delete, then click Delete
    6. All the contents of the platform will be shown on a dialogue box.
       If you want to continue deleting the platform, click ‘Delete’.
       Otherwise, click ‘Cancel’

Fig. Deleting a platform |Deleting a platform|

 ### Job Submission

Follow the steps below

    1. Navigate to the Chiminey server homepage
    2. Log in with credentials
    3. Click 'Create Job' from the menu bar
    4. Select the smart connector from the list of smart connectors
    5. Enter the values for the parameters of the selected smart
       connector. Parameters of any smart connector fall into either of
       the following types: *Computation platform, Cloud resource,
       Location, Reliability, MyTardis, Parameter Sweep* and
       *Domain-specific*. See `Types of Input Form
       Fields </chiminey/chiminey/wiki/Types-of-Input-Form-Fields/>`__
       for detailed discussion about these parameter types.
    6. Click 'Submit Job' button, then 'OK'

Fig. Submitting a job |Submitting a job|

 ### Job Monitoring

Once a job is submitted, the end-user can monitor the status of the job.

    1. Submit a job (see `Job Submission <#submitting_job>`__)
    2. Click ' Jobs'. A job status summary of all jobs will be
       displayed. The most recently submitted job is displayed at the
       top.
    3. Click 'Info' button next to each job to view a detailed status
       report.

Fig. Monitoring a job |Monitoring a job|

 ### Job Termination

The end-user can terminate already submitted jobs.

    1. Submit a job (see `Job Submission <#submitting_job>`__)
    2. Click ‘ Jobs’ to view all submitted jobs.
    3. Check the box at the end of the status summary of each job that
       you wish terminate.
    4. Click ‘Terminate selected jobs’ button. The termination of the
       selected jobs will be scheduled. Depending on the current
       activity of each job, terminating one job may take longer than
       the other.

Fig. Terminating a job |Terminating a job|

 ### Presets Management

The end-user can save the set of parameters values of a job as a preset.
Each preset must have a unique name. Using the unique preset name, the
end-user can retrieve, update and delete saved presets.

Fig. Managing presets: the drop down menu, Preset Name, is populated
with previously saved presets. |Managing presets|

Adding Preset
^^^^^^^^^^^^^

    1. Fill the parameter values for the job you are about to submit
    2. Click |'Add Preset'| next to the 'Preset Name' drop down menu
    3. Enter a unique name for the new preset
    4. Click ' Add'

Retrieving Preset
^^^^^^^^^^^^^^^^^

    1. Select the preset name from the 'Preset Name' drop down menu. The
       parameters on the submit job will be filled using parameters
       values that are retrieved from the selected preset.

Updating Preset
^^^^^^^^^^^^^^^

    1. Select the preset name from the 'Preset Name' drop down menu.
    2. Change the value of parameters as needed
    3. Save your changes by clicking |'Update Preset'| next to the
       'Preset Name' drop down menu.

Deleting Preset
^^^^^^^^^^^^^^^

    1. Select the preset name from the 'Preset Name' drop down menu.
    2. Click |'Delete Preset'|\ next to the 'Preset Name' drop down
       menu. Then, confirmation box appears.
    3. Click 'OK' to confirm.

.. |Adding cloud-based computation platform| image:: images/add_cloud_pltf.png
.. |Adding cluster/unix-based computation platform| image:: images/add_comp_pltf.png
.. |Adding unix-based storage platform| image:: images/add_unix-strg_pltf.png
.. |Adding MyTardis-based storage platform| image:: images/add_mytardis_pltf.png
.. |Updating a platform| image:: images/update_platform.png
.. |Deleting a platform| image:: images/delete_platform.png
.. |Submitting a job| image:: images/submit.png
.. |Monitoring a job| image:: images/monitor.png
.. |Terminating a job| image:: images/terminate.png
.. |Managing presets| image:: images/preset.png
.. |'Add Preset'| image:: images/add_preset.png
.. |'Update Preset'| image:: images/update_preset.png
.. |'Delete Preset'| image:: images/delete_preset.png
