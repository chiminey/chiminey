3D Surface Roughness Analysis Connector for Chiminey
====================================================

Introduction
------------
3D Surface Roughness Analysis Connector (3DRAC) allows running "3D Surface Roughness Ananysis Tool" through Chiminey. In standalone mode "3D Surface Roughness Analysis Tool" accepts an input datafile with roughness information and reports roughness qnalysis result through Java Swing GUI. However, 3DRAC connector for chiminey accepts name of the input datafile through chiminey portal.  

Chiminey portal for 3DRAC accepts a couple of inputs. The 'Data file name' field accepts a data file name that is located in the 'Input Location'. An example input data file file may be given as following:
```
0.0,   4.96   5.45   5.20   5.20   5.45
11.6,  5.45   5.20   5.20   5.69   5.69
23.2,  5.69   5.69   5.69   5.69   5.45
34.8,  5.45   5.69   5.45   5.69   5.94
46.4,  5.45   4.96   5.20   5.69   5.20
```
The input data file is taken as a cartesian plain excluding the first field in each line. The 'Virtual blocks list' field for 3DRAC in chiminey portal accepts list of virtual blocks. Flollowing is an example of a 'Virtual Blocks list' 
```
[ [0,0,4], [2,1,3], [3,3,5] ] 

```
Therefore, each block is defined by three parameters. The first parameter in the virtual block taken as X coordinate and second parameter is taken as Y cooddinate and third parameter is taken as block size. Thus virtual bloclk [2,1,3] would refer to following block in the above input data:
```
5.20   5.20   5.69
5.69   5.69   5.69
5.69   5.45   5.69
4.96   5.20   5.69
```
So, 3DRAC will extact all valid blocks and run each block against "3D Surface Roughness Analysis Tool". Depending on the internal sweep definition, each block will run on a separate process in the same VM or in different VMs in the cloud.

Farther more, 3DRAC tool will report definition of all invalid blocks and list them in a file named 'invalid_blocks_list.txt'. This file will be saved in the input directory for each individual process. Therefore, the third block definition in the above 'Virtual blocks list' is not valid accoording to above input data and will be listed in the 'invalid_blocks_list.txt'.

Farthermore, 3DRAC will check for a valid input data file and stop processing in case the input datafile is not vaild. 

3DRAC Smart Connector Core Function
-----------------------------------
A payload (http://chiminey.readthedocs.io/en/latest/payload.html#payload) provides the core functionality of 3DRAC Smart Connector. The payload structure of 3DRAC is as following:

```
payload_3drac/
|--- bootstrap.sh
|--- process_payloead
|    |---main.sh
|    |---run-rac.py
|    |---roughness-analysis-cli.jar
```
All dependencies required to prepeare the 3drac jobs execution environment is specified in the "bootstrap.sh". The "bootstrap.sh" installs appropiate version of JDK "JAVA_VERSION=jdk1.8.0_101" required by 3DRAC. To install later version of JDK,the "bootstrap.sh"script have to be modified. Please note that both JAVA is installed in "/opt" directory. Following is the content of "bootstrap.sh" for 3DRAC SC:    

```
#!/bin/sh
# version 2.0


WORK_DIR=`pwd`

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

export PATH=/opt/${JAVA_VERSION}/bin:$PATH

cd $WORK_DIR
```
The process_payload directory contains 'rougness-analysis-cli.jar, 'run-rac.py' and 'main.sh'. The jar file contains the "Roughness Analysis" tool and 'run-rac.py' is pythos scripts that extracts 'virtual blocks' from an input datafile and execute the block against 'roughness-analysis-cli.jar'. The 'main.sh' is a simple script that copies the 'roughness-analysis-cli.jar' and 'run-rac.py' to the "INPUT_DIRECTORY". It also executes the 'run-rac.py' with necessary arguments that are specific to each sweep of 3DRAC SC. Following is the content of "main.sh" for 3DRAC SC:

```
#!/usr/bin/env python
import os, sys, getopt , ast
import json

INPUT_DIR=$1
OUTPUT_DIR=$2

JAVA_HOME=/opt/jdk1.8.0_101

cp roughness-analysis-cli.jar $INPUT_DIR/roughness-analysis-cli.jar
cp run-rac.py $INPUT_DIR/run-rac.py
cd $INPUT_DIR

python run-rac.py -v values -o ../$OUTPUT_DIR -j $JAVA_HOME

# --- EOF ---
```
As mentioned earlier, "main.sh" executes "run-rac.py" and passes on necessary arguments specific to a 3DRAC job. "run-rac.py" eatracts a virtual block specific to 3DRAC job and execute 'Roughness Analysis" tool against that virtual block. Following is the content of "run-rac.py":

```
mport os, sys, getopt , ast
import json

def get_cube(valuesfile,outputdir):
   row_count = 0
   column_count = 0
   full_list =[]
   coord =[] 
   dfname =''
   
   with open(valuesfile) as json_data:
      values_content = json.load(json_data)
      coord = ast.literal_eval( values_content.get('virtual_blocks_list') ) 
      dfname = str( values_content.get('data_file_name') ) 
      #print dfname, coord 
      json_data.close()
  
   with open(dfname) as fp:
      for line in fp:
         if len(line) != 0:
            row_count += 1
            row_content = line.split()
            column_count = len(row_content) - 1
            full_list.append(row_content)
  
   x_axis = coord[0] + 1
   y_axis = coord[1]
   filename = dfname.split('.')[0] + '_' + str(coord[0]) + '_' + str(coord[1]) + '_' + str(coord[2]) + '.txt'
   filename_with_location = outputdir + '/' + filename
   with open(filename_with_location,"w") as text_file:
      for k in range(y_axis, y_axis + coord[2]):
         textline = str(full_list[k][0]) + '\t' + '\t'.join(full_list[k][ x_axis : x_axis + coord[2]]) 
         text_file.write(textline +"\n")
   return filename_with_location

def main(argv):
   valuesfile = ''
   outputdir=''
   javapath=''
   try:
      opts, args = getopt.getopt(argv,"v:o:j:",["valuesfile=","outdir=","javahome="])
   except getopt.GetoptError:
      print argv[0] + ' -v <valuesfile> -o <outputdir>'
      sys.exit(2)
   for opt, arg in opts:
      if opt in ("-o", "--outdir"):
         outputdir = arg
         #print outputdir
      elif opt in ("-v", "--valuesfile"):
         valuesfile = arg
         #print valuesfile
      elif opt in ("-j", "--javahome"):
         javapath = arg + '/bin/'
         #print javapath
   if outputdir and javapath and valuesfile:
      blockfile_withlocation = get_cube(valuesfile,outputdir)
      command_string = javapath + 'java -cp roughness-analysis-cli.jar rougness.analysis.RoughnessAnalysisCLI ' + blockfile_withlocation + ' > ' + outputdir + '/' + r'result'
      #print (command_string)
      os.system(command_string)
      return 0
   
if __name__ == "__main__":
   main(sys.argv[1:])
```

The Input Directory
-------------------
Each connector in Chiminey system may specify a payload directory that is loaded to each VM for cloud execution. This payload directory content may vary for different runs. It is done through indicating input directory for a specific run. This also allows parameteisation on the input envrionment.The input data file for "Roughness Analysis" tool nust be placed in this directory. 

Configure, Create and Execute a 3DRAC Job
------------------------------------------
"Create Job" tab in "Chiminey Portal" lists "sweep_3drac" form for creation and submission of 3drac job. "sweep_3drac" form require definition of "Compute Resource Name" and "Storage Location". Appropiate "Compute Resource" and "Storage Resource" need to be defined  through "Settings" tab in the "Chiminey portal".

A 3drac job requires two input parameters. The 'Data file name' filed requires name of the datafile that is loacted in the "Input Location". Also 'Virtual blocks list' field require a list of blocks to be extracted from the input data file. Example of virtual blocks definition is given in the 'Introduction' section.

External Sweep
--------------
To perform external sweep "3DRAC Smart Connector" in Chiminey System, splecify appropiate JSON dictionary in "Values to sweep over" field of the "sweep_3drac" form accessible through "Chiminey Portal". 

Internal Sweep
--------------
Internal sweep for "3DRAC Smart Connector" in Chiminey System may be performed by specifying the data file name in 'Data file name' field and also specifying virtual blocks list in the 'Virtual blocks list' field of the "sweep_3drac" form. 
