PRISM Smart Connector for Chiminey
==================================
Prism allows formal model checking of systems having random or probabilistic behaviour. PRISM supports experiments which is done by leaving one ome more variables undefined in prism model file.

```
const int X;
const double Y;
```
Single value or a range of values for each of these variables can be passed as command line parameters with "-const" switch.

```
prism prism-model.pm properties.pctl -const X=2:8,Y=20:80
```

Moreover, when variables in a prism model which define transition probablilties or rates left undefined and values these variables are passed as command line parameter is known as parametric model checking. 

```
const int P;
const double Q;
```
Single value or a range of values for each of these undefined variables must be passed as command line parameters with "-param" switch.

```
prism prism-model.pm properties.pctl -param P=0.2:0.8,Q=20:80
```
Therefore, executing experiments over a complex parametric prism model with several undefined variables become compute-intensive - thus make it a suitable candidate for parallel execution utilising compute resources over the cloud using Chiminey. Hence, "Prism Smart Connector for Chiminey" which allows several approach to parameter sweep i.e. internal sweep and external sweep over complex parametric prism models and thus facilitates scheduling computes over the cloud for parallel execution.

Once "Prism Smart Connector" is activated in Chiminey, Chiminey portal then allows to configure and submit a prism job for execution.

PRISM Smart Connector Core Function
-----------------------------------
A payload (http://chiminey.readthedocs.io/en/latest/payload.html#payload) provides the core functionality of PRISM SC. The payload structure of PRISM SC is as following:

```
payload_prism/
|--- bootstrap.sh
|--- process_payloead
|    |---main.sh
```
The PRISM SC needs to install Prism binary and Java runtime environment. All dependencies required to prepeare the Prism jobs execution environment is specified in the "bootstrap.sh". The "bootstrap.sh" installs PRISM  "PRISM_VERSION=4.3.1." and appropiate version of JDK "JAVA_VERSION=jdk1.8.0_101" that is required by PRISM. To install later version of PRISM and its JDK requirement, the "bootstrap.sh"script have to be modified accordingly. Please note that both PRISM and JAVA are installed in "/opt" directory. Following is the content of "bootstrap.sh" for PRISM SC:    

```
#!/bin/sh
# version 2.0

WORK_DIR=`pwd`

PRISM_VERSION=4.3.1
PRISM_DOWNLOAD_URL=http://www.prismmodelchecker.org/dl/prism-${PRISM_VERSION}-linux64.tar.gz

JAVA_UPDATE=8u101
JAVA_BUILD=b13
JAVA_VERSION=jdk1.8.0_101
JAVA_COOKIE="Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie"
JAVA_DOWNLOAD_URL="http://download.oracle.com/otn-pub/java/jdk/${JAVA_UPDATE}-${JAVA_BUILD}/jdk-${JAVA_UPDATE}-linux-x64.tar.gz"

yum -y update
yum -y install glibc.i686 libstdc++.so.6 gcc make

# Install Java
cd /opt/
wget --no-cookies --no-check-certificate --header "${JAVA_COOKIE}" "${JAVA_DOWNLOAD_URL}"
tar xzfv jdk-${JAVA_UPDATE}-linux-x64.tar.gz

# Install PRISM
cd /opt/
curl -O ${PRISM_DOWNLOAD_URL}
tar xzvf prism-${PRISM_VERSION}-linux64.tar.gz
cd prism-${PRISM_VERSION}-linux64 && ./install.sh
chown -R root:root /opt/prism-${PRISM_VERSION}-linux64
chmod -R 755 /opt/prism-${PRISM_VERSION}-linux64

export PATH=/opt/prism-${PRISM_VERSION}-linux64/bin:/opt/${JAVA_VERSION}/bin:$PATH

cd $WORK_DIR
```

The "main.sh" is a simple script that executes a shell script "run.sh" which must be already available in "INPUT_DIR". It also passes on commmand line arguments i.e. INPUT_DIR and OUTPUT_DIR to "run.sh". Recall that Chiminey sends the path to input (INPUT_DIR) and output (OUTPUT_DIR) directories via command-line arguments<payload>. Here, the SC developer passes on INPUT_DIR, where PRISM model, property and run.sh files are available, and also passes on OUTPUT_DIR where all output files will be created. Following is the content of "main.sh" for PRISM SC:

```
#!/bin/sh

INPUT_DIR=$1

sh $INPUT_DIR/run.sh $@

# --- EOF ---
```
As mentioned earlier, "main.sh" executes "run.sh" and passes on values of INPUT_DIR and OPUTPUT_DIR to it. The "run.sh" is template file that must be named as "run.sh_template" and be already made available in INPUT_DIR. "run.sh_template" will be explained further in the following paragraphs. Following is the content of "run.sh_template":

```
#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2

export PATH=/opt/jdk1.8.0_101/bin:$PATH

/opt/prism-4.3.1-linux64/bin/prism $INPUT_DIR/{{prism_model}} $INPUT_DIR/{{property_file}} {{param_string}} > $OUTPUT_DIR/result
```
So "run.sh_template" file must be located in INPUT_DIR. Since it is a template file, all template tags specified in this file will be replaced by Chiminey with corresponding values that are passed in from "Chiminey Portal" as Json dictionary. This "runs.sh_template" is renamed as "run.sh" when all template tags are replaced by corresponding values. 

"{{prism_model}}" is name of the prism model file loacated in the input directory, "{{property_file}}" is name of the property file located in the input directory, and "{{param_string}}" is the string with all parameters to be passs into PRISM. For example let's assume we have prsim model "consensus.nm", property file "consensus.pctl" located in INPUT_DIR directory, and "-m -const K=2 -param p1=0.2:0.8,p2=0.2:0.8" is the parameter string for this model. Therefore, following is the command to execute this model against PRISM:

```
/opt/prism-4.3.1-linux64/bin/prism consensus.nm consensus.pctl -m -const K=2 -param p1=0.2:0.8,p2=0.2:0.8
```  
Thus JSON dictionary to be passed from "Chiminey Protal" for above command to execute this prism model would be:

```
{ "prism_model" :  [ "consensus.nm" ], "property_file" :  [ "consensus.pctl" ], "param_string" :  [ "-m -const K=5 -param p1=0.2:0.8,p2=0.2:0.8" ] }
```

Note that "run.sh" modifies "PATH" environment variable and adds JAVA installation path "/opt/jdk1.8.0_101/bin" to it. If "bootstrap.sh" is modified to install different version of JAVA, this JAVA installation path has to be modified accordingly. Also the "run.sh" runs PRISM from PRISM installation directoy "/opt/prism-4.3.1-linux64/bin/prism". Likewise, if "bootstrap.sh" is modified to install different version of PRISM, this PRISM installation path has to be modified accordingly.

The Input Directory
-------------------
Each connector in Chiminey system may specify a payload directory that is loaded to each VM for cloud execution. This payload directory content may vary for different runs. It is done through indicating input directory for a specific run. This also allows parameteisation on the input envrionment.  Any file located in the input directory may be regarded as a template file by adding "_template" suffix. An example "run.sh" to run a specific PRISM model "consensus.nm" would be:

```
#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2

export PATH=/opt/jdk1.8.0_101/bin:$PATH

/opt/prism-4.3.1-linux64/bin/prism $INPUT_DIR/consensus.nm $INPUT_DIR/consensus.pctl -m -const K=2 -param p1=0.2:0.8,p2=0.2:0.8 > $OUTPUT_DIR/result
```
To make template "run.sh_template" for above "run.sh" for Chiminey sytem to run different PRISM model (or same PRISM model)  with different parameter set, a file named "run.sh_template" need to be created with following content and be palced in the input directory.

```
#!/bin/sh

INPUT_DIR=$1
OUTPUT_DIR=$2

export PATH=/opt/jdk1.8.0_101/bin:$PATH

/opt/prism-4.3.1-linux64/bin/prism $INPUT_DIR/{{prism_model}} $INPUT_DIR/{{property_file}} {{param_string}} > $OUTPUT_DIR/result
# --- EOF ---
```
However, corresponding "prism_model" and "property_file" must already exist in the input direcory. 

Configure, Create and Execute a Prism Job
------------------------------------------
"Create Job" tab in "Chiminey Portal" lists "prism_sweep" form for creation and submission of prism job. "sweep_prism" form require definition of "Compute Resource Name" and "Storage Location". Appropiate "Compute Resource" and "Storage Resource" need to be defined  through "Settings" tab in the "Chiminey portal".

A set of example parameterised prism models that can be readily used as input resourses in "PRISM Smart Connector for Chiminey" are available in "examples/input-resources" directory. 


External Sweep
--------------
To perform external sweep "PRISM Smart Connector" in Chiminey System, splecify appropiate JSON dictionary in "Values to sweep over" field  of the "sweep_prism" form accessible through "Chiminey Portal". An example JSON dictionary to perform external sweep for the "consensus.nm" and  "consensus.pctl" could be as following:

```
{ "prism_model" :  [ "consensus.nm" ], "property_file" :  [ "consensus.pctl" ], "param_string" :  [ "-m -const K=5 -param p1=0.2:0.8,p2=0.2:0.8" , "-m -const K=6 -param p1=0.2:0.8,p2=0.2:0.8" , "-m -const K=7 -param p1=0.2:0.8,p2=0.2:0.8" ] }
``` 

Above would create three individual process. To allocate one cloud VM for each process, input fieldis in "Cloud Compute Resource" for "sweep_prism" form has to be:

```
Number of VM instances : 1
Minimum No. VMs : 1
```
Internal Sweep
--------------
Inxternal sweep for "PRISM Smart Connector" in Chiminey System may be performed by specifying appropiate JSON dictionary in "Internal sweep map" field  of the "sweep_prism" form. An example JSON dictionary to run internal sweep for the "consensus.nm" and  "consensus.pctl" could be as following:

```
{ "prism_model" :  [ "consensus.nm" ], "property_file" :  [ "consensus.pctl" ], "param_string" :  [ "-m -const K=5 -param p1=0.2:0.8,p2=0.2:0.8" , "-m -const K=6 -param p1=0.2:0.8,p2=0.2:0.8" , "-m -const K=7 -param p1=0.2:0.8,p2=0.2:0.8" ] }
``` 
Above would create three individual process. To allocate maximum two cloud VMs - thus execute two PRISM job in same VM,  input fields in "Cloud Compute Resource" for "sweep_prism" form has to be:

```
Number of VM instances : 2
Minimum No. VMs : 1
```
A set of example sweep maps for parameterised prism models ( available at "examples/input-resource" directory) are readily available at "examples/sweep-maps" directory.

PRISM Model Source Code Reference
---------------------------------
A set of Exzample Prism models is used to test PRISM Smart Connector for Chiminey. These models are available for furtherabalysis of PRISM Smart Connector for Chiminey.

Parameterised Prism Models 
---------------------------
* Randomised Consensus Protocol

Published in:
Kwiatkowska, M; Norman, G and Segala, R
Automated verification of a randomized distributed consensus protocol Using Cadence SMV and PRISM.
In CAV, pages 194-206, Springer, LNCS 2102, 2001.

* Crowds Protocol
* Zeroconf
* Cyclic Polling Srver
* Randomised Mutual Exclusion
* Bounded Retransmission Protocol

Published in:
Hahn, Ernst Moritz and Hermanns, Holger and Zhang, Lijun 
Probabilistic reachability for parametric Markov models 
International Journal on Software Tools for Technology Transfer, Springer, 13(1), 2011.

* Die Example ( http://www.prismmodelchecker.org/tutorial/die.php)

All of the aboved models were developed to work with PARAM tool (http://depend.cs.uni-sb.de/tools/param/casestudies/). Therefore, each of these models were slightly modifilied to run as parametarised prsim model for PRISM version 4.3.1. All of these models are available in "examples/prism-models/HHZ11B" directory  

Furthermore, a couple more PRISM models were developed to verify parameterised model checking. Following Markov Chain models were used as reference :

* Figure 5.2: The papameterised DTMC of a reactive RACS (Page 66)
* Figure 5.4: The papameterised DTMC of a reactive RACS (Page 72)

The above Markov Chains were published in:
```
Iman I Yusuf,
Recovery-Oriented Software Architecture for Grid Applications (ROSA-Grids)
PhD Theses, RMIT University, March 2012
```

PRISM models for above mentioned Markov Chains are available in "examples/prism-models/IMAN" directory. Prsim models were developed by:
```
Ahmed Abdullah,
AICAUSE Lab, RMIT Universiy. November 2016
```

Graph Visualisation of PRISM Models
-----------------------------------
A 3D wareframe graph visualization tool "plot.py" has been developed to plot rational functions produced by PRISM when a parametric prism model is executed. The tool is tested with a couple of reational functions generated for parametric prism model. The tool is available in "examples/prism-models/graph-tool" directory. Execute the help command: 

```
python plot.py --help

```

The graph-tool expects two parameters i.e. parameter "-e" to specify the name of the equation file that contains rational function produced by PRISM and parameter "-v" to specify the name of the variables used in the rational function. Following are the steps to execute the graph-tool:

```
python plot.py -v mu,gamma -e output.txt
```
