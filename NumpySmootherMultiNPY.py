# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 16:34:03 2016
Need to enter 2 copies of each .npy file: 1 in /desktop/Winpython, 
and 1 in /desktop/Winpython/Tobesmoothed.
@author: ddickerson
"""

#   Numpy smoother smooths transcriptional start site plots that have been saved as Numpy arrays.
#   This script should be run using Spyder or Python on desktop.  
#   Smooths all files in a folder.

from matplotlib import pyplot as plt
import numpy as np
import os


print ('sliding window size?')
windowsize=input ()     
winsize=int(windowsize)

def process(filename):
    c=np.load(f)
    numpylength=len(c)    
    
    print (numpylength)   
    print ('^^^len of input npy^^^')
    windowmeanlist=[]
    
    i=winsize+1
    maxcoordinate=numpylength-winsize
    while i<=maxcoordinate:
        j=i+(winsize/2)
        k=i-(winsize/2)
        windowmean=(np.mean(c[k:j]))
        windowmeanlist.append(windowmean)
        i+=1
            
    np.save('SMOOTH'+f,windowmeanlist)  
    cc=len(windowmeanlist)
    print (cc)
    print ('^^^len of output npy^^^')

for f in os.listdir('//toh-smb.lifesci.dundee.ac.uk/ddickerson/Desktop/WinPython/Tobesmoothed'):
    process(f)    

