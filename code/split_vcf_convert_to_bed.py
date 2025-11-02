#!/usr/bin/env python3

"""
Written by: Jaz Sakr
Date: Nov 2025

Usage:
  python script.py input.vcf(.gz)
  
Requirements:
- Python packages: cyvcf2, pandas
- External tools: bgzip, tabix (from HTSlib)

Steps:
1. Split a single-sample phased VCF into hap1/hap2 VCFs using cyvcf2.
2. Convert each haplotype VCF into BED of ALT sites using cyvcf2.
3. Merge BEDs with colors: h1-only (green), h2-only (orange), shared (purple).
4. Validate that the total ALT sites match the original VCF.

This will create the following output files based on the input basename:
  <prefix>_h1.vcf.gz
  <prefix>_h2.vcf.gz
  <prefix>_h1_vcf.bed.gz
  <prefix>_h2_vcf.bed.gz
  <prefix>_vcf_browser.bed.gz
  (and all corresponding .tbi index files)

"""

from cyvcf2 import VCF, Writer
import pandas as pd
import subprocess
import sys
import os

__version__ = "1.0.0"

def run_cmd(cmd):
    """Executes a shell command."""
    #print(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)


### Step 1: Split haplotypes (using cyvcf2) ###

def split_haplotypes(in_vcf, out1_vcf_gz, out2_vcf_gz):
    vcf_in = VCF(in_vcf)

    # cyvcf2.Writer writes uncompressed. Write to a temp file,
    # then bgzip and rename it to the final .gz
    out1_vcf_tmp = out1_vcf_gz.replace(".vcf.gz", ".tmp.vcf")
    out2_vcf_tmp = out2_vcf_gz.replace(".vcf.gz", ".tmp.vcf")

    hap1_out = Writer(out1_vcf_tmp, vcf_in)
    hap2_out = Writer(out2_vcf_tmp, vcf_in)

    print(f"Splitting {in_vcf} into {out1_vcf_gz} and {out2_vcf_gz} ...")
    for v in vcf_in:
        if not v.genotypes:
            print(f"Warning: Skipping record with no samples at {v.CHROM}:{v.start+1}")
            continue

        # v.genotypes[0] is [allele1, allele2, phased_boolean]
        # cyvcf2 uses -1 for a missing allele ('.')
        g = v.genotypes[0]
        left, right, phased = g[0], g[1], g[2]

        # Handle missing ('.') alleles, which are -1 in cyvcf2
        if left == -1: left = -1
        if right == -1: right = -1

        # hap1
        v.genotypes = [[left, left, phased]]
        hap1_out.write_record(v)

        # hap2
        v.genotypes = [[right, right, phased]]
        hap2_out.write_record(v)

    hap1_out.close()
    hap2_out.close()
    vcf_in.close()

    # Now bgzip and tabix the outputs
    for tmp_file, gz_file in [(out1_vcf_tmp, out1_vcf_gz), (out2_vcf_tmp, out2_vcf_gz)]:
        run_cmd(f"bgzip -f {tmp_file}")
        run_cmd(f"mv {tmp_file}.gz {gz_file}")
        run_cmd(f"tabix -f -p vcf {gz_file}")

    print(f"Split VCF bgzipped + tabixed: {out1_vcf_gz}, {out2_vcf_gz}")


### Step 2: Create BED from VCF (using cyvcf2) ###

def vcf_to_bed(vcf_gz, bed_out_gz):
    vcf = VCF(vcf_gz)

    # Write to a temporary UNCOMPRESSED file first
    bed_out_tmp = bed_out_gz.replace(".gz", "")

    with open(bed_out_tmp, "w") as f:
        for v in vcf:
            if not v.gt_types: # Skip if no GT info
                continue

            # v.gt_types[0] is 0 (HOM_REF), 1 (HET), 2 (HOM_ALT), 3 (UNKNOWN)
            # Get ALT sites (1 or 2)
            if v.gt_types[0] > 0:
                # cyvcf2 is 0-based, so v.start is POS-1 and v.end is POS.
                f.write(f"{v.CHROM}\t{v.start}\t{v.end}\n")

    vcf.close()

    # Now bgzip and tabix the outputs
    run_cmd(f"bgzip -f {bed_out_tmp}")
    run_cmd(f"tabix -f -p bed {bed_out_gz}")
    print(f"BED bgzipped + tabixed: {bed_out_gz}")

def count_original_alt_sites(in_vcf):
    """Counts all HET or HOM_ALT sites in the original VCF."""
    print(f"\nCounting original VCF: Counting ALT sites in {in_vcf} ...")
    vcf_in = VCF(in_vcf)
    count = 0
    for v in vcf_in:
        if v.gt_types[0] > 0: # 0=HOM_REF, 1=HET, 2=HOM_ALT
            count += 1
    vcf_in.close()
    print(f"Found {count} original ALT sites (HET or HOM_ALT).")
    return count

### Step 3: Merge and create color-coded BED ###

def merge_colored_beds(h1_bed_gz, h2_bed_gz, out_bed_gz):
    """Merges two BED files and assigns colors to SNPs."""
    print(f"Merging {h1_bed_gz} and {h2_bed_gz} into {out_bed_gz} ...")
    try:
        h1 = pd.read_csv(h1_bed_gz, sep="\t", header=None, names=["chrom","start","end"])
    except pd.errors.EmptyDataError:
        print(f"Warning: {h1_bed_gz} is empty.")
        h1 = pd.DataFrame(columns=["chrom","start","end"])

    try:
        h2 = pd.read_csv(h2_bed_gz, sep="\t", header=None, names=["chrom","start","end"])
    except pd.errors.EmptyDataError:
        print(f"Warning: {h2_bed_gz} is empty.")
        h2 = pd.DataFrame(columns=["chrom","start","end"])

    if h1.empty and h2.empty:
        print("Warning: Both input BED files are empty.")
        return 0, 0, 0 # Return 0 for all counts

    # Create a unique key for merging
    h1["key"] = h1["chrom"] + ":" + h1["start"].astype(str) + "-" + h1["end"].astype(str)
    h2["key"] = h2["chrom"] + ":" + h2["start"].astype(str) + "-" + h2["end"].astype(str)

    shared_keys = set(h1["key"]).intersection(h2["key"])
    h1_only = h1[~h1["key"].isin(shared_keys)]
    h2_only = h2[~h2["key"].isin(shared_keys)]
    shared = h1[h1["key"].isin(shared_keys)]

    # Get counts for validation
    h1_only_count = len(h1_only)
    h2_only_count = len(h2_only)
    shared_count = len(shared)

    def make_bed(df, label, color):
        if df.empty:
            return pd.DataFrame() # Return empty DF if no sites
        df = df.copy()
        df["label"] = label
        df["score"] = 0 # Column 5: score
        df["strand"] = "." # Column 6: strand
        df["thickStart"] = df["start"] # Column 7: thickStart
        df["thickEnd"] = df["end"] # Column 8: thickEnd
        df["color"] = color # Column 9: itemRgb
        # Standard BED9 format
        return df[["chrom","start","end","label","score","strand","thickStart","thickEnd","color"]]

    merged = pd.concat([
        make_bed(h1_only, 1, "0,255,0"), # h1 is green color
        make_bed(h2_only, 2, "255,165,0"), # h2 is orange color
        make_bed(shared, " ", "128,0,128") # homozygous SNP is purple
    ])

    if merged.empty:
        print("Warning: No sites found to merge.")
        return 0, 0, 0 # Return 0 for all counts

    merged.sort_values(["chrom","start"], inplace=True)

    tmp_bed = out_bed_gz.replace(".gz","")
    merged.to_csv(tmp_bed, sep="\t", header=False, index=False)

    # Now bgzip and tabix the outputs
    run_cmd(f"bgzip -f {tmp_bed}")
    run_cmd(f"tabix -f -p bed {tmp_bed}.gz")
    print(f"Merged colored BED bgzipped + tabixed: {out_bed_gz}")

    return h1_only_count, h2_only_count, shared_count

### Main ###

def main():
    print(f"Version {__version__}")
    
    # Check for correct number of arguments
    if len(sys.argv) != 2:
        print(f"\nUsage: python {os.path.basename(__file__)} input.vcf(.gz)")
        print("  This will auto-generate all output files based on the input prefix.")
        sys.exit(1)

    infile = sys.argv[1]

    # Get base output name
    base_name = infile
    if base_name.endswith(".vcf.gz"):
        base_name = base_name[:-7] # remove .vcf.gz
    elif base_name.endswith(".vcf"):
        base_name = base_name[:-4] # remove .vcf

    # Define all output file paths
    hap1_vcf_gz = f"{base_name}_h1.vcf.gz"
    hap2_vcf_gz = f"{base_name}_h2.vcf.gz"
    h1_bed_gz = f"{base_name}_h1_vcf.bed.gz"
    h2_bed_gz = f"{base_name}_h2_vcf.bed.gz"
    merged_bed_gz = f"{base_name}_vcf_browser.bed.gz"

    # Stop if ANY output files already exist
    files_to_check = [hap1_vcf_gz, hap2_vcf_gz, h1_bed_gz, h2_bed_gz, merged_bed_gz]
    existing_files = [f for f in files_to_check if os.path.exists(f)]

    if existing_files:
        print(f"\nError: The following output files already exist:")
        for f in existing_files:
            print(f"  {f}")
        print(f"\nPlease remove them by running:")
        print(f"rm {' '.join([f + '*' for f in existing_files])}")
        sys.exit(1)

    original_alt_count = count_original_alt_sites(infile)
    if original_alt_count == 0:
        print("Warning: No ALT sites found in original VCF.")
        sys.exit(0)

    # Step 1: split haplotypes
    print(f"\nSplitting VCF into haplotypes ...")
    split_haplotypes(infile, hap1_vcf_gz, hap2_vcf_gz)

    # Step 2: convert to BED
    print(f"\nConverting split VCFs to BED ...")
    vcf_to_bed(hap1_vcf_gz, h1_bed_gz)
    vcf_to_bed(hap2_vcf_gz, h2_bed_gz)

    # Step 3: merge colored BEDs
    print(f"\nCreating merged SNP color-coded BED ...")
    h1_count, h2_count, shared_count = merge_colored_beds(h1_bed_gz, h2_bed_gz, merged_bed_gz)

    # Step 4: validation
    print("\nValidation:")
    print(f"Original VCF ALT sites: {original_alt_count}")
    print(f"Hap1-only sites:  {h1_count}")
    print(f"Hap2-only sites:  {h2_count}")
    print(f"Shared sites:     {shared_count}")

    merged_total = h1_count + h2_count + shared_count
    print(f"Total merged sites: {merged_total}")

    if original_alt_count == merged_total:
        print(f"\nSUCCESS: Original VCF count matches merged BED count.")
    else:
        print(f"\nFAILURE: Original VCF count ({original_alt_count}) does NOT match merged BED count ({merged_total}).")

    print("\nAll steps completed successfully.")

if __name__ == "__main__":
    main()
