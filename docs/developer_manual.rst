================
Developer Manual
================




.. _smart_connector_desc:

Smart Connector: the core concept within Chiminey
---------------------------------------------------


A smart connector is composed of at least seven predefined core stages:
configure, create, bootstrap, schedule, execute, wait and destroy.
Depending of the expected functionality of a smart connector, one or
more of the core stages may need to be customised, and/or other stages
may need to be added. All core stages are located under
``chiminey/corestages``.

In general, creating a smart connector involves

-  customising existing and/or adding new stages as needed,
-  defining the smart connector based on these stages, and
-  registering the smart connector within Chiminey.





.. toctree::

   :titlesonly:

   chimineyui
   payload
   examples
