#!/bin/bash
#SBATCH -A SEYEDAM_LAB
#SBATCH --partition=standard
#SBATCH --mem=50G
#SBATCH --cpus-per-task=1
#SBATCH --time=06:00:00
#SBATCH --job-name=minimap2
#SBATCH -o minimap2_o%A.log
#SBATCH -e minimap2_e%A.log
#SBATCH --mail-type=fail,end
#SBATCH --mail-user=email@uci.edu

sample=$1
genome=$2

ref="/user/reference/"
fastq="/user/nanopore/fshd/fastqs/"
output="/user/nanopore/fshd/analysis/"

# this is a commented out line

module load minimap2/2.17

minimap2 \
-t 16 \
-ax map-ont \
--MD \
--secondary=no \
${ref}${genome} \
${fastq}${sample}".fastq" > \
${output}${sample}"_mapped.sam"
