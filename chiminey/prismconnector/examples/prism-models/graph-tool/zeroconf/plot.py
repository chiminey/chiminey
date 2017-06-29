#!/usr/bin/python
# -*- coding: utf-8 -*-

# Developed by Ahmed Abdullah,
# AICAUSE Lab, RMIT Universiy. November 2016

from __future__ import division
import sys, getopt, ast
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
from numpy import exp,arange
from pylab import meshgrid,cm,imshow,contour,clabel,colorbar,axis,title,show


def validate_equation(vars, eqstr):
  if len(eqstr.split(':')) > 2:
    prefix = 1
  else:
    prefix = 0
  limits = ast.literal_eval(eqstr.split(':')[prefix].replace('(','').replace(')','').strip())
  eq = eqstr.split(':')[prefix+1].replace('^','**').replace('{','').replace('}','').strip().split()
  indexlist = []
  print "Original equation: "
  print eq 
  i = 0
  while i < len(eq)-1:
    #print eq[i]
    if eq[i].isdigit():
      #print '========'
      #print "eq[i] : " +eq[i]
      #print "eq[i+1] : " +eq[i+1]
      if eq[i+1].find(vars[0]) or eq[i+1].find(vars[1]):
        #print "vars[0] : " + vars[0]
        #print "vars[1] : " + vars[1]
        #print eq[i+1]
        if eq[i+1] != '|':
          indexlist.append(i)
    i = i + 1
  #print indexlist
  k = 0
  for j in indexlist:
    k=k+1
    eq.insert(j+k,'*') 
  eq = ' '.join(eq)
  eq =  eq.strip()

  eq = eq.split('|')
  top = eq[0].strip().split()
  top.insert(-len(top),'(')
  top.append(')')
  top = ' '.join(top)
  bottom = eq[1].strip().split()
  bottom.insert(-len(bottom),'(')
  bottom.append(')')
  bottom = ' '.join(bottom)
  eq[0] = top
  eq[1]= bottom
  eq = '/'.join(eq)

  return (limits,eq)

# the function that I'm going to plot
def z_function(X,Y,varList,equation):
 print "\n    Variables list :", varList
 print "\n    Equation :\n    ", equation
 equation = equation.replace(varList[0],'X')
 print "\n    Variables mapping:"
 print "        '%s' mapped to X" %(varList[0])
 equation = equation.replace(varList[1],'Y')
 print "        '%s' mapped to Y" %(varList[1])
 print "\n    Calculating Z axis by evaluating equation:\n    %s"%(equation)
 return (eval(equation))

def main(argv):
   variableslist = ''
   equationfile = ''
   equation = ''
   try:
      opts, args = getopt.getopt(argv,"hv:e:",["variables=","equation="])
   except getopt.GetoptError:
      print argv[0] + ' -v <variableslist> -e <equationfile>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print argv[0] + ' -v <variableslist> -e <equationfile>'
         sys.exit()
      elif opt in ("-v", "--variables"):
         variableslist = arg.split (",")
      elif opt in ("-e", "--equation"):
         #print arg
         fo = open ( arg , "r+" )
         for line in fo:
           #print line
           if line.find('{') > 0:
             equation = line
             #print equation
         fo.close
   (limits,equation) = validate_equation(variableslist,equation)

   precision = 0.05
   #x = arange(0,1,precision)
   #y = arange(0,1,precision)

   print "\nWill arrange X axis as: %s with %f"%(limits[0], precision)
   x = arange(limits[0][0],limits[0][1],precision)

   print "\nWill arrange X axis as: %s with %f"%(limits[1], precision)
   y = arange(limits[1][0],limits[1][1],precision)

   X,Y = meshgrid(x, y) # grid of point

   print "\nWill calculate Z axis:"
   Z = z_function(X, Y,variableslist,equation) # evaluation of the function on the grid

   fig = plt.figure()
   ax = fig.gca(projection='3d')
   #ax = fig.add_subplot(111, projection='3d')

   print "\n\nPlotting wareframe graph... .. .\n\n"
   ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1)

   plt.show()

if __name__ == "__main__":
   main(sys.argv[1:])
