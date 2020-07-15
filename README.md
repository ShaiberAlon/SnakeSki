# SnakeSki
Collection of Snakemake workflow for data analysis jobs commonly done in mski Lab

## Usage

```
snakemake -s $hg19_core_pipeline \
          --configfile config.json \
          --jobs $N
```

Where:
 - `config.json` is the configuration file (more details below).
 - `N` - Number of jobs to run in parallel.
 - `hg19_core_pipeline` is the path to the core pipeline Snakefile.

 ## The config file

The config file contains the path to the pairs table and to relevant task files.

For example:

```json
{
    "pairs_rds": "path-to-pairs-rds-file" ,
    "oncotable": {
        "task": "~/tasks/hg19/core_dryclean/Oncotable.task"
        }
}
```
