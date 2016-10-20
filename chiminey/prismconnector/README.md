Prism Connector Install instructions
====================================


Install Chiminey and PRISM Connector
------------------------------------


* Install chiminey via http://github.com/chiminey/docker-chiminey

* use the ```prism``` branch of ```docker-chiminey``` repository.

* Copy ```prismconnector``` directory into ```/opt/chiminey/current/chiminey/```




Setup Chiminey for PRISM connectors
-----------------------------------

* Add to ```SMART_CONNECTORS``` in ```settings.py```

```
         'prism':   {'init': 'chiminey.prismconnector.initialise.PrismInitial',
             'name': 'prism',
             'description': 'The PRISM Model Checker',
             'payload': '/opt/chiminey/current/chiminey/prismconnector/payload_prism',
             'sweep': True
             },
```    

* Add to ```INPUT_FILES``` in ```settings.py```

```
    'mytardis':  SCHEMA_PREFIX + "/input/mytardis",
    'prism':  SCHEMA_PREFIX + "/input/prism",
```

* Then activate the connector with
```
./activatesc prism
```


Create PRISM server
-------------------

* Create a PRISM docker container if needed:

```
cd prismserver
docker-compose up -p
```  

This prism server is accessible by SSH at localhost:38000

* Add a reference to this server as a HPC computation resource in chiminey.
