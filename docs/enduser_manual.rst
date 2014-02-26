================
 Enduser Manual
================
An end-user submits a smart connector job, monitors the job, visualises
job results and publishes the result to the public BDP index. In this
documentation, following topics are covered:

* :ref:`getting_chiminey_account`

* :ref:`login`

* :ref:`logout`

* :ref:`configure_platform_settings`

* `Submitting a job`_

* `Monitoring a job`_

* `Terminating a job`_

* `Managing presets`_

.. _getting_chiminey_account:

Getting Chiminey Account
------------------------

Chiminey accounts are managed by admin users. Therefore, in order to get
access to a specific Chiminey server, the end-user should contact the
admin of the Chiminey server.

.. _login:

Login
------------------------

End-users login via the web interface of the Chiminey server

1. Click 'login' on the home page
2. Enter Chiminey credentials
3. Click 'Login'

.. figure:: img/enduser_manual/login.png

.. _logout:

Logout
------------------------

1. click 'Logout

.. figure:: img/enduser_manual/logout.png


.. _configure_platform_settings:

Platform Settings Configuration
------------------------

A Chiminey server supports two types of platforms: computation and
storage. A computation platform is where the core functionality of a
smart connector is executed while a storage platform is the destination
of the smart connector output. Prior to submitting a job, end-users need
to register at least one computation and one storage platforms. In this
section, following topics are covered:

-  :ref:`register_computation_platform`
-  :ref:`register_storage_platform`
-  :ref:`update_platform`
-  :ref:`delete_platform`


.. _register_computation_platform:

Registering Computation Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Two types of computation platforms can be registered within the Chiminey
UI. The types are :ref:`cloud_comp_pltf` and :ref:`cluster_unix_platform`.

.. _cloud_platform:

Cloud Computation Platform
""""""""

1.  Navigate to the Chiminey server homepage
2.  Log in with credentials
3.  Click ``Settings``
4.  Click ``Computation Platform`` from the ``Settings`` menu
5.  Click ``Add Computation Platform``
6.  Click the ``Cloud`` tab.
7.  Select the platform type from the drop down menu. You may have  access to more than one type of cloud service, e.g., NeCTAR and Amazon.
8.  Enter a unique platform name. This name should be something you could remember.
9.  Enter credentials such as EC2 access key and EC2 secret key
10. You can optionally enter the VM image size
11. Click ``Add``. The newly added cloud-based computation platform will be displayed.

Fig. Adding cloud-based computation platform |Adding cloud-based
computation platform|

.. _cluster_unix_platform:

Cluster/Unix
""""""""

1.  Navigate to the Chiminey server homepage
2.  Log in with credentials
3.  Click ``Settings``
4.  Click ``Computation Platform`` from the ``Settings`` menu
5.  Click ``Add Computation Platform``
6.  Click the ``Cluster/Unix`` tab.
7.  Enter a unique platform name. This name should be something you could remember.
8.  Enter IP address or hostname of the cluster head node or any Unix server
9.  Enter credentials, i.e. username and password. Password is not stored in the Chiminey server. It is temporarily kept in memory Chiminey server to the computation platform.
10. Enter homepath. This is the location where .ssh directory resides. The home path is needed to store a public key on the cluster head node or the unix server.
11. Enter rootpath. The root path is used as the working directory during execution.
12. Click ``Add``
13. The newly added computation platform will be displayed under ``Cluster/Unix`` list.

Fig. Adding cluster/unix-based computation platform |Adding
cluster/unix-based computation platform|

Registering Storage Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Two types of storage platforms can be registered within the Chiminey UI. The types are :ref:`unix_storage_platform` and :ref:`mytardis_storage_platform`.

.. _unix_storage_platform:

Unix
"""""

1.  Navigate to the Chiminey server homepage
2.  Log in with credentials
3.  Click ``Settings``
4.  Click ``Storage Platform`` from the ``Settings`` menu
5.  Click ``Add Storage Platform``
6.  Click the ``Unix`` tab.
7.  Enter a unique platform name. This name should be something you could remember.
8.  Enter IP address or hostname of the unix-based storage
9.  Enter credentials, i.e. username and password. Password is not stored in the Chiminey server. It is temporarily kept in memory to to establish a private/public key authentication from the Chiminey server to the storage.
10. Enter homepath. This is the location where ``.ssh`` directory resides. The home path is needed to store a public key on the unix server.
11. Enter rootpath. The root path is used as the working directory of the Chiminey server.
12. Click ``Add``
13. The newly added storage platform will be displayed under ``Unix`` list.

Fig. Adding unix-based storage platform |Adding unix-based storage
platform|

.. _mytardis_storage_platform:

MyTardis
""""""

1.  Navigate to the Chiminey server homepage
2.  Log in with credentials
3.  Click ``Settings``
4.  Click ``Storage Platform`` from the ``Settings`` menu
5.  Click ``Add Storage Platform``
6.  Click the ``MyTardis`` tab.
7.  Enter a unique platform name. This name should be something you could remember.
8.  Enter IP address or hostname of the MyTardis instance
9.  Enter credentials, i.e. username and password. Username and password are stored on the Chiminey server.
10. Click ``Add``
11. The newly added storage platform will be displayed under MyTardis list.

Fig. Adding MyTardis-based storage platform |Adding MyTardis-based
storage platform|


Updating Computation/Storage Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Navigate to the Chiminey server homepage
2. Log in with credentials
3. Click ``Settings``
4. To update a computation platform, click ``Computation Platform`` whereas to update a storage platform, click ‘Storage Platform’ from the ``Settings`` menu.
5. Locate the platform you wish to update, then click ``Update``
6. Make the changes, and when finished click ``Update``

Fig. Updating a platform |Updating a platform|


Deleting Computation/Storage Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Navigate to the the Chiminey server homepage
2. Log in with credentials
3. Click ``Settings``
4. To delete a computation platform, click ``Computation Platform`` whereas to delete a storage platform, click ``Storage Platform`` from the ‘Settings’ menu.
5. Locate the platform you wish to delete, then click Delete
6. All the contents of the platform will be shown on a dialogue box. If you want to continue deleting the platform, click ``Delete``. Otherwise, click ``Cancel``

Fig. Deleting a platform |Deleting a platform|
