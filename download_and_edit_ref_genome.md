# Download and edit references
ALL Gencode reference versions:
Index of /pub/databases/gencode/Gencode_human/
http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/

UCSC Dec. 2013 assembly of the human genome CHROMOSOMES
https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/

## genome
[TALON-paper-2019](https://github.com/dewyman/TALON-paper-2019)/[refs](https://github.com/dewyman/TALON-paper-2019/tree/master/refs)/**[download_and_index_human_genome.sh](https://github.com/dewyman/TALON-paper-2019/blob/master/refs/download_and_index_human_genome.sh)**

Download GRCh38_no_alt_analysis_set_GCA_000001405.15.fasta.gz, unzip and remove extra information from fasta headers with `awk '{print $1}'`
command:
```bash
wget https://www.encodeproject.org/files/GRCh38_no_alt_analysis_set_GCA_000001405.15/@@download/GRCh38_no_alt_analysis_set_GCA_000001405.15.fasta.gz
gunzip GRCh38_no_alt_analysis_set_GCA_000001405.15.fasta.gz
awk '{print $1}' GRCh38_no_alt_analysis_set_GCA_000001405.15.fasta > GRCh38.v29_ENCODE_genome.fa
```

NOTE: other wise you will get an error when running TranscriptClean.py: `RuntimeError: One or more SAM chromosomes were not found in the fasta reference.`

### create index
make .fai file on .fa file above using samtools
```bash
module load samtools
samtools faidx GRCh38.v29_ENCODE_genome.fa
```

## annotation gtf file

Download gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz and unzip
GENCODE v29 comprehensive gene annotation (reference chromosomes only). https://www.gencodegenes.org/human/release_29.html
```bash
wget https://www.encodeproject.org/files/gencode.v29.primary_assembly.annotation_UCSC_names/@@download/gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz
gunzip gencode.v29.primary_assembly.annotation_UCSC_names.gtf.gz
mv gencode.v29.primary_assembly.annotation_UCSC_names.gtf GRCh38.v29_gencode_genome.annotation.gtf
```

version 28
```bash
wget http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_28/gencode.v28.primary_assembly.annotation.gtf.gz
gunzip gencode.v28.primary_assembly.annotation.gtf.gz
paftools.js gff2bed gencode.v28.primary_assembly.annotation.gtf > gencode.v28.primary_assembly.annotation.bed
```

### make bed file
for mapping with minimap2, this only needs to be done once per reference:
>Since v2.17, minimap2 can optionally take annotated genes as input and prioritize on annotated splice junctions. To use this feature, you can
>`paftools.js gff2bed anno.gff > anno.bed`
> `minimap2 -ax splice --junc-bed anno.bed ref.fa query.fa > aln.sam`
>Here, anno.gff is the gene annotation in the GTF or GFF3 format (gff2bed automatically tests the format). The output of gff2bed is in the 12-column BED format, or the BED12 format. With the --junc-bed option, minimap2 adds a bonus score (tuned by --junc-bonus) if an aligned junction matches a junction in the annotation. Option --junc-bed also takes 5-column BED, including the strand field. In this case, each line indicates an oriented junction.

Use minimap2’s utility [paftools.js](https://github.com/lh3/minimap2/blob/master/misc/README.md#introduction) to convert the annotation file from gtf to bed file.
```bash
module load minimap2
paftools.js gff2bed GRCh38.v29_gencode_genome.annotation.gtf > GRCh38.v29_gencode_genome.annotation.bed
```

## create sj file
[TALON-paper-2019](https://github.com/dewyman/TALON-paper-2019)/[refs](https://github.com/dewyman/TALON-paper-2019/tree/master/refs)/[make_splice_references.sh](https://github.com/dewyman/TALON-paper-2019/blob/master/refs/make_splice_references.sh)

```bash
gtf="GRCh38.v29_gencode_genome.annotation.gtf"
genome="GRCh38.v29_ENCODE_genome.fa"
sj_file="GRCh38.v29_ENCODE_genome.sj"

python ~/TranscriptClean//accessory_scripts/get_SJs_from_gtf.py \
--f=${gtf} \
--g=${genome} \
--o=${sj_file}
```

## download common variants

[TALON-paper-2019](https://github.com/dewyman/TALON-paper-2019)/[refs](https://github.com/dewyman/TALON-paper-2019/tree/master/refs)/[download_commonSNPs.sh](https://github.com/dewyman/TALON-paper-2019/blob/master/refs/download_commonSNPs.sh)

common human variants from dbSNP Build150 (April 2017 release). https://www.ncbi.nlm.nih.gov/variation/docs/human_variation_vcf/)

```bash
# Download common variants to use with TranscriptClean
# The subset of 00-All categorized as common (minor allele frequency >= 0.01 in at least one of 26 major populations, with at least two unrelated individuals having the minor allele)". https://www.ncbi.nlm.nih.gov/variation/docs/human_variation_vcf/
wget ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606/VCF/00-common_all.vcf.gz

# Change chromosome convention so that chromosomes start with 'chr'
zcat 00-common_all.vcf.gz | awk '{if($0 !~ /^#/ && $0 !~ /^chr/) print "chr"$0; else print $0}' > tmp_00-common_all.vcf
gzip tmp_00-common_all.vcf
mv tmp_00-common_all.vcf.gz common-variants_human_dbSNP-Build150.vcf.gz
```
