#!/bin/bash -l
source ~/.bashrc
#. /usr/share/Modules/init/bash

# Script parses through a bam file and pulls out reads with specified lengths, here thresholds are min length 20, max 80bp.
# Saves these reads to new bam file.

# Adjust tlen window with the $9 values below 

module load samtools
samtools view -h 1386a252.bam | awk '$1~"@" || $9 >= 20 && $9 <= 80'| samtools view -Sh - > tlen2080.sam
cut -f9 tlen2080.sam > 1386a252tlen2080.txt   		#outputs column 9 (tlen) to .txt file
sed 's/ \+/,/g' 1386a252tlen2080.txt > 1386a252tlen2080.csv 	#converts .txt file to .csv file





