
.. _configure_platform_settings:

Platform Settings Configuration
===============================


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
--------------------------------


Two types of computation platforms can be registered within the Chiminey
UI. The types are :ref:`cloud_comp_pltf` and :ref:`cluster_unix_platform`.

.. _cloud_platform:

Cloud Computation Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey server homepage
#.  Log in with credentials
#.  Click ``Settings``
#.  Click ``Computation Platform`` from the ``Settings`` menu
#.  Click ``Add Computation Platform``
#.  Click the ``Cloud`` tab.
#.  Select the platform type from the drop down menu. You may have  access to more than one type of cloud service, e.g., NeCTAR and Amazon.
#.  Enter a unique platform name. This name should be something you could remember.
#.  Enter credentials such as EC2 access key and EC2 secret key
#. You can optionally enter the VM image size
#. Click ``Add``. The newly added cloud-based computation platform will be displayed.


.. figure:: img/enduser_manual/add_cloud_pltf.png
    :align: center
    :alt: Adding cloud-based computation platform
    :figclass: align-center

    Figure. Adding cloud-based computation platform


.. _cluster_unix_platform:

Cluster/Unix  Computation Platform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey server homepage
#.  Log in with credentials
#.  Click ``Settings``
#.  Click ``Computation Platform`` from the ``Settings`` menu
#.  Click ``Add Computation Platform``
#.  Click the ``Cluster/Unix`` tab.
#.  Enter a unique platform name. This name should be something you could remember.
#.  Enter IP address or hostname of the cluster head node or any Unix server
#.  Enter credentials, i.e. username and password. Password is not stored in the Chiminey server. It is temporarily kept in memory Chiminey server to the computation platform.
#. Enter homepath. This is the location where .ssh directory resides. The home path is needed to store a public key on the cluster head node or the unix server.
#. Enter rootpath. The root path is used as the working directory during execution.
#. Click ``Add``
#. The newly added computation platform will be displayed under ``Cluster/Unix`` list.


.. figure:: img/enduser_manual/add_comp_pltf.png
    :align: center
    :alt: Adding cluster/unix-based computation platform
    :figclass: align-center

    Figure. Adding cluster/unix-based computation platform


.. _register_storage_platform:

Registering Storage Platform
----------------------------

Two types of storage platforms can be registered within the Chiminey UI. The types are :ref:`unix_storage_platform` and :ref:`mytardis_storage_platform`.

.. _unix_storage_platform:

Unix Storage Platform
^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey server homepage
#.  Log in with credentials
#.  Click ``Settings``
#.  Click ``Storage Platform`` from the ``Settings`` menu
#.  Click ``Add Storage Platform``
#.  Click the ``Unix`` tab.
#.  Enter a unique platform name. This name should be something you could remember.
#.  Enter IP address or hostname of the unix-based storage
#.  Enter credentials, i.e. username and password. Password is not stored in the Chiminey server. It is temporarily kept in memory to to establish a private/public key authentication from the Chiminey server to the storage.
#. Enter homepath. This is the location where ``.ssh`` directory resides. The home path is needed to store a public key on the unix server.
#. Enter rootpath. The root path is used as the working directory of the Chiminey server.
#. Click ``Add``
#. The newly added storage platform will be displayed under ``Unix`` list.


.. figure:: img/enduser_manual/add_unix-strg_pltf.png
    :align: center
    :alt: Adding unix-based storage platform
    :figclass: align-center

    Figure. Adding unix-based storage platform


.. _mytardis_storage_platform:

MyTardis Storage Platform
^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey server homepage
#.  Log in with credentials
#.  Click ``Settings``
#.  Click ``Storage Platform`` from the ``Settings`` menu
#.  Click ``Add Storage Platform``
#.  Click the ``MyTardis`` tab.
#.  Enter a unique platform name. This name should be something you could remember.
#.  Enter IP address or hostname of the MyTardis instance
#.  Enter credentials, i.e. username and password. Username and password are stored on the Chiminey server.
#. Click ``Add``
#. The newly added storage platform will be displayed under MyTardis list.


.. figure:: img/enduser_manual/add_mytardis_pltf.png
    :align: center
    :alt:  Adding MyTardis-based storage platform
    :figclass: align-center

    Figure.  Adding MyTardis-based storage platform


.. _update_platform:

Updating Computation/Storage Platform
-------------------------------------


#. Navigate to the Chiminey server homepage
#. Log in with credentials
#. Click ``Settings``
#. To update a computation platform, click ``Computation Platform`` whereas to update a storage platform, click ‘Storage Platform’ from the ``Settings`` menu.
#. Locate the platform you wish to update, then click ``Update``
#. Make the changes, and when finished click ``Update``


.. figure:: img/enduser_manual/update_platform.png
    :align: center
    :alt:  Updating a platform
    :figclass: align-center

    Figure.  Updating a platform

.. _delete_platform:

Deleting Computation/Storage Platform
-------------------------------------


#. Navigate to the the Chiminey server homepage
#. Log in with credentials
#. Click ``Settings``
#. To delete a computation platform, click ``Computation Platform`` whereas to delete a storage platform, click ``Storage Platform`` from the ‘Settings’ menu.
#. Locate the platform you wish to delete, then click Delete
#. All the contents of the platform will be shown on a dialogue box. If you want to continue deleting the platform, click ``Delete``. Otherwise, click ``Cancel``


.. figure:: img/enduser_manual/delete_platform.png
    :align: center
    :alt:  Deleting a platform
    :figclass: align-center

    Figure.  Deleting a platform

