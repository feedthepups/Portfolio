#!/bin/bash
#source ~/.bash_profile
#. /usr/share/Modules/init/bash


# This script takes 2 arguments.  First is input bam filename.
# Second is the samflag/binary number from https://broadinstitute.github.io/picard/explain-flags.html. 
# Samflag 1820 tosses duplicates and unaligned seqs. 

#To run:    qsub -cwd PrimaryAlignmentDuplicatesRemoved.sh 1386a25head 1820


samtools view -b -F $2 -h "$1".bam -o "$1"DR_PA.bam 
samtools sort -O BAM -o "$1"_s.bam "$1DR_PA.bam" 
rm "$1DR_PA.bam"
samtools index "$1"_s.bam
mv "$1"_s.bam "$1"2head.bam
mv "$1"_s.bam.bai "$1"2head.bam.bai


echo "Duplicates removed :)"

echo "--------------------------------------------------------------------------------"
echo "DONE"
echo "--------------------------------------------------------------------------------"

	
