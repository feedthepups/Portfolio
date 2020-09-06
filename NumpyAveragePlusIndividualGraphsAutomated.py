#!/bin/env python

  
# Input several numpy arrays describing different nucleosome positioning curves, output curve that is mean of these arrays,
# as well as the individual arrays.

import sys as sys; import numpy as np; from matplotlib import pyplot as plt;  import os; import fnmatch; import pandas as pd

ii=[]; j=0; c=[]; file_count=0;
zz=0


print ('How many curves do you wish to average?')
Curves=raw_input() #Curves=input ()
curves=int(Curves)
while zz<curves:

    print ('name of curve'); print curves; print('?')
    Curve1=input ()
    zz+=1


def filecount(foldername):         #take the count of all the files in folder

    file_count = len(fnmatch.filter(os.listdir('H:/Desktop/WinPython/ToBeAveraged'), '*.npy'))
    #print (file_count, 'yay')
    return file_count     #  seems to work up to this point.
    
def fileload(filename):         #load all of the files
    #ii.append(f)  #.astype(np.str)

    df1=pd.DataFrame()
    #need to turn f into a string.
    aa=str(f)
    print (f)
    print (aa)
    df1.append(aa)

    return aa
 
def filemean(c):    

    c = [(df1[j])/(file_count) for j in range(1402)] 
    print ('3')
    np.save('outcrap.npy', c)
    return c
    #print (c)
#countfiles(ii)    
    
for f in os.listdir('H:\Desktop\WinPython\ToBeAveraged'):

    filecount(file_count)
    print (file_count)
    fileload(f)
    df2=pd.DataFrame()
    df2=df2.append(f)
    print (6)
    print (file_count, 'booo')

filemean(c)
   
# now plot the mean as a thick black line, and other curves normally.
xx=np.arange(1402)

plt.ion()
plt.plot(np.load('outcrap.npy')) #xx,c, color='k',linewidth=2)
#plt.plot(xx,ii)
#plt.plot(xx,jj)
#plt.plot(xx,kk)
#plt.plot(xx,ll)

sys.exit

#def countfiles(counter):        #need to count number of files to take mean
    #x=(os.listdir('/lifesci/groups/toh/ddickerson/Analysis/2017_08_09/NPYfiles/Raw')

    #path, dirs, files = os.walk('H:\Desktop\WinPython\ToBeAveraged').__next__()
    #path, dirs, files = os.walk('H:\Desktop\WinPython\ToBeAveraged').next()
    #file_count = len(files)

    

    
