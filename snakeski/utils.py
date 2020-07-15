# -*- coding: utf-8
# pylint: disable=line-too-long

import os
import time
import snakeski
import subprocess

import pandas as pd

from snakeski import filesnpaths
from snakeski.errors import ConfigError

__author__ = "Alon Shaiber"
__credits__ = ["Adopted partly from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__version__ = snakeski.__version__
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


def format_cmdline(cmdline):
    """Takes a cmdline for `run_command` or `run_command_STDIN`, and makes it beautiful."""
    if not cmdline or (not isinstance(cmdline, str) and not isinstance(cmdline, list)):
        raise ConfigError("You made ultis::format_cmdline upset. The parameter you sent to run kinda sucks. It should be string\
                            or list type. Note that the parameter `shell` for subprocess.call in this `run_command` function\
                            is always False, therefore if you send a string type, it will be split into a list prior to being\
                            sent to subprocess.")

    if isinstance(cmdline, str):
        cmdline = [str(x) for x in cmdline.split(' ')]
    else:
        cmdline = [str(x) for x in cmdline]

    return cmdline


def run_command(cmdline, log_file_path, first_line_of_log_is_cmdline=True, remove_log_file_if_exists=True):
    """Uses subprocess.call to run your `cmdline`"""

    cmdline = format_cmdline(cmdline)

    filesnpaths.is_output_file_writable(log_file_path)

    if remove_log_file_if_exists and os.path.exists(log_file_path):
        os.remove(log_file_path)

    try:
        if first_line_of_log_is_cmdline:
            with open(log_file_path, "a") as log_file: log_file.write('# DATE: %s\n# CMD LINE: %s\n' % (get_date(), ' '.join(cmdline)))

        log_file = open(log_file_path, 'a')
        ret_val = subprocess.call(cmdline, shell=False, stdout=log_file, stderr=subprocess.STDOUT)
        log_file.close()

        if ret_val < 0:
            raise ConfigError("command was terminated")
        else:
            return ret_val
    except OSError as e:
        raise ConfigError("command was failed for the following reason: '%s' ('%s')" % (e, cmdline))


def save_pairs_table_as_TAB_delimited(pairs_rds, pairs_TAB_delimited_path=None):
    ''' Reads the pairs table from the rds file and stores it in a TAB delimited format'''

    # Before we do anything let's make sure the user has R installed
    is_program_exists('Rscript')

    # Let's make sure all the required packages are installed
    missing_packages = []
    required_packages = ["data.table", "optparse"]

    log_file = filesnpaths.get_temp_file_path()
    for lib in required_packages:
        ret_val = run_command(["Rscript", "-e", "library('%s')" % lib], log_file)
        if ret_val != 0:
            missing_packages.append(lib)

    if missing_packages:
        raise ConfigError('The following R packages are required in order to run \
                           this program, but are missing: %s.' % ', '.join(missing_packages))

    if not pairs_TAB_delimited_path:
        pairs_TAB_delimited_path = filesnpaths.get_temp_file_path()

    log_file = filesnpaths.get_temp_file_path()
    print(log_file)
    cmd = 'store-pairs-table-as-TAB-delimited.R -p %s -o %s' % (pairs_rds, pairs_TAB_delimited_path)
    print(cmd)
    run_command(cmd, log_file)

    # returning the path to the TAB-delimited file in case it was created here as a temp file and is needed for a downstream process
    return(pairs_TAB_delimited_path)


def is_program_exists(program, dont_raise=False):
    IsExe = lambda p: os.path.isfile(p) and os.access(p, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if IsExe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = os.path.expanduser(path).strip('"')
            exe_file = os.path.join(path, program)
            if IsExe(exe_file):
                return exe_file

    if dont_raise:
        return False

    raise ConfigError("The following software: '%s' needs to be installed on your system, but it doesn't seem to appear\
                        in your path :/ If you are certain you have it on your system (for instance you can run it\
                        by typing '%s' in your terminal window), you may want to send a detailed bug report. Sorry!"\
                        % (program, program))


def get_path_to_snakeski_dir():
    # this returns a path
    base_path = os.path.dirname(__file__)
    return base_path


def get_date():
    return time.strftime("%d %b %y %H:%M:%S", time.localtime())


def get_task_column_names():
    return ['io_type', 'param', 'param_name_in_pairs_table', 'param_type', 'default_value']


def load_param_table_from_task_file(task_file, number_of_lines_to_skip=2):
    ''' Load the parameters from the task file as a data frame'''

    f = open(task_file).read().splitlines()
    # skipping commented lines
    f = [s for s in f if not s.startswith('#')]
    # skipping the line in which the module is mentioned
    f = f[1:]

    # converting sequences of spaces to tabs
    task_lines = ['\t'.join(s.split()) for s in f[2:]]

    col_names = get_task_column_names()
    d = pd.DataFrame(index = range(len(task_lines)), columns = col_names)
    for i in d.index:
        cols = col_names.copy()
        cols.reverse()
        for s in task_lines[i].split('\t'):
            c = cols.pop()
            d.loc[i,c] = s

    return d


def get_default_task_file_path():
    return '~/.default_task_files.json'
