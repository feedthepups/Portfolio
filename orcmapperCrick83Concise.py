#!/bin/env python

#  This script generates a .npy file that can be used to map nucleosome Crick-strand-specific reads from nascent chromatin flanking replication origins.

import scipy
import csv
import numpy
import sys as sys
import pysam
import pandas as pd


def _pandas_read_csv(csvfile):
    _df0=pd.read_csv(csvfile,sep=',' )     
    _chrm=list(_df0['chro'].tolist()) 
    _start=list(_df0['orcstrt'].tolist())
    _end=list(_df0['orcend'].tolist())
    _strand=list(_df0['strnd'].tolist())
    _mid=list(_df0['mid'].tolist())
    return _chrm,_start,_end,_strand,_mid        
    

def bamfil_orc(sbamfile):
    path='/lifesci/groups/toh/ddickerson/Analysis/2017_12_07seqs/'+aaa+'/'

    input_bamfile=sbamfile+'Crick83.bam'
    bamfile=pysam.Samfile(path+input_bamfile,"rb")        
    total=bamfile.mapped			     
    chrmb,ori,end,strand,middle=_pandas_read_csv('/lifesci/groups/toh/ddickerson/RegionalData/ORCpositions15.csv')    

    nuc_reads=scipy.zeros(2001)
    counter=0
    forwardcounter=0
    reversecounter=0
    while counter < len(chrmb):
        cordinate_data=scipy.zeros(2001)
        try: 
            for reads in bamfile.fetch(str(chrmb[counter]),int(middle[counter])-1100,int(middle[counter])+1100): 
		   
                    if reads.is_reverse:     #
                        coord=(reads.pos-int(abs(reads.tlen)/2))+reads.rlen  
                        reversecounter+=1
                    else:
                        forwardcounter+=1   #
                        coord=reads.pos+int(reads.tlen/2)                                                         
                    postn=coord-(int(middle[counter])-1000)   
		    if postn>=0:     
                        try:
                                cordinate_data[postn]+=1
                        except IndexError:  
                                pass

        except (IndexError, ValueError):  
            pass
        if str(strand[counter])== "+":
            #forwardcounter+=1
            pass
        else:
            nuc_reads+=(cordinate_data[::-1]) 
            #reversecounter+=1
        
        counter+=1
    print forwardcounter
    print ('forwardcounter^^^')
    print  reversecounter
    print (' ^^^reversecounter^^^^')
    print nuc_reads
    print ('1st nuc_reads^^^')
    nuc_reads.astype(float)      
    meaner=(float(numpy.mean(nuc_reads)))
    print meaner
    print ('meaner^^^')
    output=nuc_reads/meaner #(total/12100000.0)  #Normalized Amanda's way   ((nuc_reads)/(total/genomesize)) =? counts/(read depth/genome size)
   
    numpy.save('/lifesci/groups/toh/ddickerson/Analysis/2017_12_07seqs/'+aaa+'/'+sbamfile+'_'+'_Crick83orc.npy',output)
    print output
    print ('output^^^')
    return output



aaa=(sys.argv[1])
bamfil_orc(aaa)

sys.exit
