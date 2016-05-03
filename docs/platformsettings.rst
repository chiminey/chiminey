
.. _configure_platform_settings:

Resource  Management
===============================


A Chiminey platform  supports access to computation and
storage resources. A computation resource is where the core functionality of a
smart connector is executed while a storage resource is used to retrieve input files and store output files.
 Prior to submitting a job, end-users need
to register at least one computation and one storage resources. In this
section, following topics are covered:

-  :ref:`register_computation_resource`
-  :ref:`register_storage_platform`
-  :ref:`update_platform`
-  :ref:`delete_platform`


.. _register_computation_resource:

Registering Compute Resource
----------------------------


Various computing infrastructure and tools can be registered as compute resources. These resources are broadly categorised under    :ref:`cloud <cloud_resource>`, :ref:`high performance computing (HPC) <hpc_resources>`,
:ref:`analytics <analytics_resource>`,  and continuous integration resources.


.. _cloud_resource:

Cloud Compute Resource
^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey portal.
#.  Log in with your credentials.
#.  Click ``Settings``.
#.  Click ``Compute Resource`` from the ``Settings`` menu.
#.  Click ``Register Compute Resource``
#.  Click the ``Cloud`` tab.
#.  Select the resource type from the drop down menu. You may have  access to more than one type of cloud service, e.g., NeCTAR and Amazon.
#.  Enter a unique resource name.
#.  Enter credentials such as EC2 access key and EC2 secret key
#.  Click ``Register``. The newly registered  cloud-based compute resource will be displayed under `Cloud - NeCTAR/CSRack/Amazon EC2`.


.. figure:: img/enduser_manual/cloud_register.png
    :align: center
    :alt: Registering a cloud-based compute resource
    :figclass: align-center

    Figure. Registering a cloud-based compute resource


.. _hpc_resource:

HPC Compute Resource
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey portal.
#.  Log in with your credentials.
#.  Click ``Settings``.
#.  Click ``Compute Resource`` from the ``Settings`` menu.
#.  Click ``Register Compute Resource``
#.  Click the ``HPC`` tab.
#.  Enter a unique resource name.
#.  Enter IP address or hostname of the HPC cluster head node or the standalone server.
#.  Enter credentials, i.e. username and password. Password is not stored in the Chiminey platform. It is temporarily kept in memory to establish a private/public key authentication from the Chiminey platform to the resource.
#.  Click ``Register``.  The newly registered resource will be displayed under `HPC - Cluster or Standalone Server` list.


.. figure:: img/enduser_manual/hpc_register.png
    :align: center
    :alt: Registering a HPC compute resource
    :figclass: align-center

    Figure. Registering a HPC compute resource


.. _analytics_resource:

HPC Compute Resource
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#.  Navigate to the Chiminey portal.
#.  Log in with your credentials.
#.  Click ``Settings``.
#.  Click ``Compute Resource`` from the ``Settings`` menu.
#.  Click ``Register Compute Resource``
#.  Click the ``Analytics`` tab.
#.  Select ``Hadoop MapReduce`` as the resource type from the drop down menu.
#.  Enter a unique resource name.
#.  Enter IP address or hostname of the Hadoop MapReduce resource.
#.  Enter username and password. Password is not stored in the Chiminey platform. It is temporarily kept in memory to establish a private/publi key authentication from the Chiminey platform to the resource.
#.  Click ``Register``.  The newly registered resource will be displayed under `Analytics - Hadoop MapReduce` list.


.. figure:: img/enduser_manual/analytics_register.png
    :align: center
    :alt: Registering an analytics compute resource (Hadoop MapReduce)
    :figclass: align-center

    Figure. Registering an analytics compute resource (Hadoop MapReduce)



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
