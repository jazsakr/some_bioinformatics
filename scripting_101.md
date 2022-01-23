[[embedded_images/sample_script_anno.png]]
# Section 1
The HPC3 uses a SLURM scheduler and that is why we have to put `#SBATCH`. This is called a **bash header** and it provides instructions to the SLURM. This bash header **MUST**	be included at the top of every bash script.

## Here is what each line means:

`#!/bin/bash` --> this MUST be the first line

`-A SEYEDAM_LAB` --> who to charge money for the job

`--partition=standard` --> indicates that this is a paid job, not free

`--mem=50G` --> request 50G of memory

`--cpus-per-task=1` --> request 1 CPU

`--time=06:00:00` --> run job for no more than 6 hrs

`--job-name=minimap2` --> the name of the job (just for our convenience)

`-o minimap2_o%A.log` --> request standard output log with job number

`-e minimap2_e%A.log` --> request standard error log with job number

`--mail-type=fail,end` --> send an email when job fails or ends

`--mail-user=jsakr@uci.edu` --> which email to send to

# Section 2
This section assigns **variables** to the **command line arguments**. This essentially allows you to use a script as a template with fill-in-the-blank like capabilities. When you submit the job through the command line, you will provide information that fills in the blanks, called **command line arguments**. You could have as many arguments as you want.

An example application would be using a script designed in this way: to
1. map multiple samples with the same parameters
2. keep the same parameters but change reference genomes
3. and more

NOTE: order of the command line arguments is **IMPORTANT**! In our example, if we want to assign our sample name to the variable `sample`, we must list it as the first command line argument because `$1` means that the first command line argument will be assigned to the variable `sample`.

for our sample script, submitting it will look like this in the terminal:
```bash
sbatch sample_script.sh sample1 human_genome.fa
```

# Section 3
This section tells the HPC were all the files it need to run the job is located.

To make things easier and cleaning, we will also be assigning the files along with its location to a **variable**. Just like how we assigned the command line arguments to a variable in Section 2.
