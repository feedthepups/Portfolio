#!/bin/env python

#  This script generates a .npy file that can be used to map nucleosome Watson-strand-specific reads from nascent chromatin flanking replication origins.

import scipy
import csv
import numpy
import sys as sys
import pysam
import pandas as pd

#   bds=bamfil_region_cord(sys.argv[1],sys.argv[2],sys.argv[3])

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

    input_bamfile=sbamfile+'Watson2.bam'
    bamfile=pysam.Samfile(path+input_bamfile,"rb")    
    total=bamfile.mapped			      
    chrmb,ori,end,strand,middle=_pandas_read_csv('/lifesci/groups/toh/ddickerson/RegionalData/ORCpositions15.csv')    

    nuc_reads=scipy.zeros(2001)
    counter=0
    snoreF=0
    snoreR=0
    while counter < len(chrmb):
        cordinate_data=scipy.zeros(2001)
        try:  #This is necessary if TSS is near end of chromosome
            for reads in bamfile.fetch(str(chrmb[counter]),int(middle[counter])-1100,int(middle[counter])+1100): 
		   
                    if reads.is_reverse:    # This picked up 906519 reads.
                        coord=(reads.pos-int(abs(reads.tlen)/2))+reads.rlen    
		
                        snoreR+=1
                    else:           # This didn't pick up any reads.
                        coord=reads.pos+int(reads.tlen/2)    
                        snoreF+=1
                    postn=coord-(int(middle[counter])-1000)   
		    if postn>=0:      # Need this because Python uses 2 systems for identifying numbers in a list: 0, +1, +2 = positions from left side of the list.
			    	      #  -1, -2 = positions from right side of list.  Some of the position numbers we generate will be negative in value, so these
				      #need to be dropped.  This is done by only taking positions>0.
                        try:
                                cordinate_data[postn]+=1
                        except IndexError:  #positions that are outside of the sliding window will generate an index error, so these will be dropped.  These two methods (index error and postn>=0) 
					    #determine the cutoff positions of the sliding window.
                                pass

        except (IndexError, ValueError):  #This is necessary if TSS is near end of chromosome
            pass
        if str(strand[counter])== "+":
            nuc_reads+=cordinate_data #pass #nuc_reads+=cordinate_data     #Appends + strand list values to nuc_reads
        else:
            nuc_reads+=(cordinate_data[::-1])  #Inverts reverse strand list, appends to nuc_reads
        
        counter+=1
    print snoreF
    print "^^^snoreF^^^"
    print snoreR
    print "^^^snoreR^^^"
    print nuc_reads
    print ('1st nuc_reads^^^')
    nuc_reads.astype(float)       
    meaner=(float(numpy.mean(nuc_reads)))
    print meaner
    print ('meaner^^^')
    output=nuc_reads/meaner #(total/12100000.0)  #Normalized Amanda's way   ((nuc_reads)/(total/genomesize)) =? counts/(read depth/genome size)
    numpy.save('/lifesci/groups/toh/ddickerson/Analysis/2017_12_07seqs/'+aaa+'/'+sbamfile+'_'+'_Watsonorc147.npy',output)
    print output
    print ('output^^^')
    return output

#Now call the functions
aaa=(sys.argv[1])
#print aaa   works up to here
bamfil_orc(aaa)

sys.exit
