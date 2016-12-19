JMT Smart Connector for Chiminey
==================================

Introduction:
------------
JMT comes along with several Java Modelling Tools (JMT) named as JMVA, JSIM , JMCH, etc. These modeling tools allow designing Network Queueing Models(NQM) and run various expariments on them. The NQM designed through JMT GUI are saved as an intermediary texfile in XML format. Since model file corresponding to JMVA and JSIM tools be run from command line, only these two types of models can be executed through Chiminey.

JMVA for Chiminey - JMVA tool saves the model files as <model_file.jmva> and can be executed from command line as:
```
  java -cp JMT.JAR jmt.commandline.Jmt mva <model_file.jmva >.
```

The JMVA tool for JMT SC only need two parameters (from Chiminey web portal) to execute JMVA tool specific model file:
```
* Model file name: model_file.jmva ; a valid .jmva model file in XML format
* JMT Tool: JMVA ; name of the JMT tool 
```

JSIM for Chiminey - JSIM tool saves the model files as <model_file.jsimg> and can be executed from command line as:
```
  java -cp JMT.JAR jmt.commandline.Jmt sim <model_file.jsimg> [options].
```

Thus, JMT connector for chiminey just need two parameters from Chiminey web portal to execute a .jsimg model file against JSIM tool.
```
* 'Model file name' : model_file.jsimg ; a valid .jsimg model file in XML format
* 'JMT Tool' : JSIM ; name of the JMT tool 
```

However, there are couple of options specific to JSIM tools that can be set from Chiminey portal:
```
* 'JSIM simulation seed' : 4567 ;  to set the simulation seed to 4567
* 'JSIM MaxTime' : 120 ; to set the maximum simulation time to 120 seconds
```

Example of a command line with options:
```
  java -cp JMT.JAR jmt.commandline.Jmt sim model_name.jsimg -maxtime 120 -seed 4567
```

Parameter sweeps for JMVA & JSIM - farthermore, JMT allows to set values for model parameters - that can be changed from GUI for each tool i.e. JMVA, JSIM etc. - and run experiments. The same can be achieved automatically through Chiminey executing parameter sweeps. For example to define one closed class with N = 10 and one open class with λ = 0.5,  the XML code for JMVA tool will be:
```
  <classes number=”2”>
     <closedclass name=”ClosedClass” population=”10”/>
     <openclass name=”OpenClass” rate=”0.5”/>
  <classes>
```

The above section can be farther parameterisd with chiminey to do parameter sweeps on the values of N or λ. Let us define a tag for value of N as following:
```
  <classes number=”2”>
     <closedclass name=”ClosedClass” population=”{{class_population_1}}”/>
     <openclass name=”OpenClass” rate=”0.5”/>
  <classes>
```

Thus value for {{class_population_1}} tag can be parameterised and can be defined as JSON dictionary. The Chiminey portal for JMT connector allows to define "Additional parameter sweeps" field. Thus a valid JSON dictinary for "{{class_population_1}} tag will be as following:
```
  {'class_population_1' : [ 20, 40, 80] }
```

The above parameter sweep definition would ensure three seperate runs of JMVA process each having a different value for 'class_population_1' tag.

JMT Smart Connector Core Function
---------------------------------
A payload (http://chiminey.readthedocs.io/en/latest/payload.html#payload) provides the core functionality of JMT Smart Connector (SC). The payload structure of JMT SC is as following:

```
payload_jmtc/
|--- bootstrap.sh
|--- process_payload
|    |---main.sh
```
The JMT SC needs to install JMT jar and Java runtime environment. All dependencies required to prepeare the JMT connector's jobs execution environment is specified in the "bootstrap.sh". The "bootstrap.sh" installs JMT, "JMT_VERSION=0.9.4" and appropiate version of JDK, "JAVA_VERSION=jdk1.8.0_101". To install later version of JMT and its JDK requirement, the "bootstrap.sh"script have to be modified accordingly. Please note that both JMT and JAVA are installed in "/opt" directory. Following is the content of "bootstrap.sh" for JMTC SC:    

```
#!/bin/sh
# version 2.0


WORK_DIR=`pwd`

JMT_VERSION=0.9.4
JMT_DOWNLOAD_URL=https://sourceforge.net/projects/jmt/files/jmt/JMT-${JMT_VERSION}/JMT-singlejar-${JMT_VERSION}.jar

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

# Install JMT
cd /opt/
curl -L ${JMT_DOWNLOAD_URL} > JMT.jar

export PATH=/opt/${JAVA_VERSION}/bin:$PATH

cd $WORK_DIR
```

The "main.sh" is a simple script that executes a shell script "run.sh" which must be already available in "INPUT_DIR". It also passes on commmand line arguments i.e. INPUT_DIR and OUTPUT_DIR to "run.sh". Recall that Chiminey sends the path to input (INPUT_DIR) and output (OUTPUT_DIR) directories via command-line arguments<payload>. Here, the SC developer passes on INPUT_DIR, where JMT model file and run.sh files are available, and also passes on OUTPUT_DIR where all output files will be moved. Following is the content of "main.sh" for JMTC SC:

```
#!/bin/sh

INPUT_DIR=$1

cd $INPUT_DIR

sh run.sh $@

# --- EOF ---
```
As mentioned earlier, "main.sh" executes "run.sh" and passes on values of INPUT_DIR and OPUTPUT_DIR to it. The "run.sh" is template file that must be named as "run.sh_template" and be already made available in INPUT_DIR. "run.sh_template" will be explained further in the following paragraphs. Following is the content of "run.sh_template":

```
#!/bin/sh
# version 2.0

INPUT_DIR=$1
OUTPUT_DIR=$2

JAVA_HOME=/opt/jdk1.8.0_101

JMT_TOOL={{jmtconnector_jmt_tool}}
MODEL_FILE={{jmtconnector_model_file}}
JSIM_SEED={{jmtconnector_jsim_seed}}
JSIM_MAXTIME={{jmtconnector_jsim_maxtime}}

if [ "${JMT_TOOL}" == "JMVA" ]
then
    echo "$JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt mva ${MODEL_FILE}" > stdout.log
    $JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt mva ${MODEL_FILE} >> stdout.log 2>&1
elif [ "${JMT_TOOL}" == "JSIM" ]
then
    if [ "${JSIM_MAXTIME}" != "0" ] && [ "${JSIM_SEED}" != "0" ]
    then
        echo "$JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -maxtime ${JSIM_MAXTIME} -seed ${JSIM_SEED}" > stdout.log
        $JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -maxtime ${JSIM_MAXTIME} -seed ${JSIM_SEED} >> stdout.log 2>&1
    elif [ "${JSIM_MAXTIME}" != "0" ] && [ "${JSIM_SEED}" == "0" ]
    then
        echo "$JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -maxtime ${JSIM_MAXTIME}" > stdout.log
        $JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -maxtime ${JSIM_MAXTIME} >> stdout.log 2>&1
    elif [ "${JSIM_MAXTIME}" == "0" ] && [ "${JSIM_SEED}" != "0" ]
    then
        echo "$JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -seed ${JSIM_SEED}" > stdout.log
        $JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} -seed ${JSIM_SEED} >> stdout.log 2>&1
    elif [ "${JSIM_MAXTIME}" == "0" ] && [ "${JSIM_SEED}" == "0" ]
    then
        echo "$JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE}" > stdout.log
        $JAVA_HOME/bin/java -cp /opt/JMT.jar jmt.commandline.Jmt sim ${MODEL_FILE} >> stdout.log 2>&1
    fi
    cp ~/JMT/jSIM.log ../$OUTPUT_DIR
fi

mv ${MODEL_FILE}-result* ../$OUTPUT_DIR
mv stdout.log ../$OUTPUT_DIR
```
So "run.sh_template" file must be located in INPUT_DIR. Since it is a template file, all template tags specified in this file will be replaced by Chiminey with corresponding values that are passed in from "Chiminey Portal" This "runs.sh_template" is renamed as "run.sh" after all template tags are replaced by corresponding values. 

'JMT Tool' field in JMT SC in Chiminey portal is internally recognised as "{{jmtconnector_jmt_tool}}", it is name of the JMT tool that chiminey will execute - only JMVA or JSIM are valid values for this field. 'Model file name' field in JMT SC in Chiminey portal is internally recognised as {{jmtconnector_model_file}} - it is name of the model file loacated in the input directory, 'JSIM simulation seed' filed in JMT SC in Chiminey portal is internally recognised as "{{jmtconnector_jsim_seed}}", it is the value for optional parameter '-seed' for JSIM tool, and 'JSIM MaxTime' field in JMT SC in Chiminey portal is internally recognised as "{{jmtconnector_jsim_maxtime}}", it is the value for optional parameter the '-maxtime' for JSIM tool. 

Note that JAVA_HOME path is set to "/opt/jdk1.8.0_101". If "bootstrap.sh" is modified to install different version of JAVA, this JAVA_HOME path has to be modified accordingly. Also the "run.sh" runs JMT.jar from JMT installation directoy "/opt". Likewise, "bootstrap.sh" need to be modified to install different version of JMT.

The Input Directory
-------------------
The iput directory for JMT SC need to have the run.sh_template file that we describe earlier. Also the input directoy need to have a valid model file either for JMVA or for JSIM tool. The file name located in this directory must me specified in the 'Model file name' field in Chiminey portal.

Configure, Create and Execute a Prism Job
------------------------------------------
"Create Job" tab in "Chiminey Portal" lists "jmtc_sweep" form for creation and submission of jmtc job. "sweep_jmtc" form require definition of "Compute Resource Name" and "Storage Location". Appropiate "Compute Resource" and "Storage Resource" need to be defined  through "Settings" tab in the "Chiminey portal".

A set of example jmt models that can be readily used as input resourses in "JMT Smart Connector for Chiminey". JMT installation come along with example models and are available in "JMT/examples". 


External Sweep
--------------
To perform external sweep "JMT Smart Connector" in Chiminey System, splecify appropiate JSON dictionary in "Values to sweep over" field  of the "sweep_jmt" form accessible through "Chiminey Portal". As described in the introduction section, for example to define one closed class with N = 10 and one open class with λ = 0.5,  the XML code for JMVA tool will be:
```
<classes number=”2”>
   <closedclass name=”ClosedClass” population=”10”/>
   <openclass name=”OpenClass” rate=”0.5”/>
<classes>
```
The above section can be farther parameterisd with chiminey to do parameter sweeps on the values of N or λ. Let us define a tag for value of N as following:
```
<classes number=”2”>
   <closedclass name=”ClosedClass” population=”{{class_population_1}}”/>
   <openclass name=”OpenClass” rate=”0.5”/>
<classes>
```
Thus value for {{class_population_1}} tag can be parameterised and can be defined as JSON dictionary. The Chiminey portal for JMT connector allows to define external sweep in "values to sweep over" field. Thus a valid JSON dictinary for "{{class_population_1}} tag will be as following:
```
{'class_population_1' : [ 20, 40, 80] }
```
The above parameter sweep definition would allocate three separate VMs each to run a seperate JMVA process having a different value for 'class_population_1' tag.
However, To allocate one cloud VM for each process, input fieldis in "Cloud Compute Resource" for "sweep_jmtc" form has to be:

```
Number of VM instances : 1
Minimum No. VMs : 1
```
Internal Sweep
--------------
Please follow 'Additional sweep parameters' definition from the introduction section.
