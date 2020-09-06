#!/bin/env python

#  This script plots nucleosome positions at ABF1 transcription factor binding sites.
#  Input is a bam file containing nucleosomal DNA NGS reads.
#  Output is .npy

import scipy
import csv
import numpy
import sys as sys
import pysam
import pandas as pd
import os

def process(filename):
    if filename!=('*.bai'):  # or '*~':
        print filename
        print ('running^^^')

        def _pandas_read_csv(csvfile):
            _df0=pd.read_csv(csvfile,sep=',' )      
            _chr=list(_df0['chro'].tolist()) 
            _center=list(_df0['newAbf1site'].tolist())
            _class=list(_df0['gene'].tolist())
            _strand=list(_df0['strnd'].tolist())         
            return _chr,_center,_class,_strand       

        def bamfil_orc(sbamfile):
            print ('6')
            path='/lifesci/groups/toh/ddickerson/Analysis/TestFolder/bamfiles/'
        
            input_bamfile=filename  #sbamfile+'.bam'
            print filename
            bamfile=pysam.Samfile(path+input_bamfile,"rb")    
            total=bamfile.mapped			     
        
            chrmb,center1,Classific,strand=_pandas_read_csv('/lifesci/groups/toh/ddickerson/RegionalData/Abf1BindingSites.csv')   
            nuc_reads=scipy.zeros(2101)
            counter=0
            print ('7')
            while counter < len(chrmb):
                cordinate_data=scipy.zeros(2101)
                try: 
                    for reads in bamfile.fetch(str(chrmb[counter]),int(center1[counter])-1050,int(center1[counter])+1050):  
                        if reads.is_reverse:
                            coord=(reads.pos-int(abs(reads.tlen)/2))+reads.rlen    
                        else:
                            coord=reads.pos+int(reads.tlen/2)                                                           
                            postn=coord-(int(center1[counter])-1050)   
        		    if postn>=0:     
                                try:
                                    cordinate_data[postn]+=1
                                except IndexError:  
                                    pass
        
                except (IndexError, ValueError):  
                    pass
                if str(strand[counter])== "+":
                    nuc_reads+=cordinate_data    
                else:
                    nuc_reads+=(cordinate_data[::-1]) 
                
                counter+=1
            print ('8')
            print nuc_reads
            print ('1st nuc_reads^^^')
            nuc_reads.astype(float)       
            meaner=(float(numpy.mean(nuc_reads)))
            print meaner
            print ('meaner^^^')
            output=nuc_reads/meaner  
            output2=output[50:2101]    
            numpy.save('/lifesci/groups/toh/ddickerson/Analysis/'+TestFolder+'/NPYfilesAbf1/'+sbamfile+'_'+'_Abf1.npy',output2)
            print output2
            print ('output2^^^')
            print(len(output2))
            print ('len output2^^^')
            
            return output2
        
        
        bamfil_orc(filename)   # +'2')
    else:     #filename=='*.bam':
        print ('5')
        print filename
        print ('not running^^^')
        pass
for f in os.listdir('/lifesci/groups/toh/ddickerson/Analysis/TestFolder/bamfiles'):
    process(f)   

sys.exit
