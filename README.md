# SnakeSki
Collection of Snakemake workflow for data analysis jobs commonly done in mski Lab. These workflows are designed to be compatible with [Flow](https://github.com/mskilab/flow) modules.

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

## Installation

SnakeSki workflows require Python 3 (recommended: version 3.7).

### Installing from github using virtual environment

The recommended way to install these workflows is using a virtual environment.

You can set a virtual environment:

```bash
python -m venv /path/to/virtual/env
```

Going forward this text will assume your virtual environment is set up here: `~/virtual-envs/SnakeSki`:

```bash
python -m venv ~/virtual-envs/SnakeSki
```



Then activate it:

```
source ~/virtual-envs/SnakeSki/bin/activate
```

get a clone of the github repository:

```bash
git clone https://github.com/ShaiberAlon/SnakeSki.git
```

Notice: that from here on the text will assume you cloned the code to the following location:

```
~/git/SnakeSki
```

Install dependencies:

```bash
cd SnakeSki
pip install -r requirements.txt
```

```
# updating the activation script for the Python virtual environmnet
# so (1) Python knows where to find SnakeSki libraries, (2) BASH knows
# where to find its programs, and (3) every time the environment is activated
# it downloads the latest code from the `master` repository
echo -e "\n# >>> SnakeSki STUFF >>>" >> ~/virtual-envs/SnakeSki/bin/activate
echo 'export PYTHONPATH=$PYTHONPATH:~/git/SnakeSki/' >> ~/virtual-envs/SnakeSki/bin/activate
echo 'export PATH=$PATH:~/git/SnakeSki/bin:~/git/SnakeSki/sandbox' >> ~/virtual-envs/SnakeSki/bin/activate
echo 'cd ~/git/SnakeSki && git pull && cd -' >> ~/virtual-envs/SnakeSki/bin/activate
echo "# <<< ANVI'O STUFF <<<" >> ~/virtual-envs/SnakeSki/bin/activate
```
