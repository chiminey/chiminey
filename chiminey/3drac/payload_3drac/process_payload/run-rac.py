#!/usr/bin/env python
import os, sys, getopt , ast
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
