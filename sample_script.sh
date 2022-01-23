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
#SBATCH --mail-user=jsakr@uci.edu

sample=$1
genome=$2

ref="/dfs3b/samlab/jsakr/reference/"
fastq="/share/crsp/lab/seyedam/jsakr/nanopore/fshd/fastqs/"
output="/share/crsp/lab/seyedam/jsakr/nanopore/fshd/analysis/"

module load minimap2/2.17

minimap2 \
-t 16 \
-ax map-ont \
--MD \
--secondary=no \
${ref}${genome} \
${fastq}${sample}".fastq" > \
${output}${sample}"_mapped.sam"
