# -*- coding: utf-8
# pylint: disable=line-too-long

import os
import subprocess

from snakeski import filesnpaths

__author__ = "Alon Shaiber"
__credits__ = ["Adopted partly from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


def run_command(cmdline, log_file_path, first_line_of_log_is_cmdline=True, remove_log_file_if_exists=True):
    """Uses subprocess.call to run your `cmdline`"""

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
        utils.is_program_exists('Rscript')

        # Let's make sure all the required packages are installed
        missing_packages = []
        required_packages = ["data.table"]

        log_file = filesnpaths.get_temp_file_path()
        for lib in required_packages:
            ret_val = utils.run_command(["Rscript", "-e", "library('%s')" % lib], log_file)
            if ret_val != 0:
                missing_packages.append(lib)

        if missing_packages:
            raise ConfigError('The following R packages are required in order to run \
                               this program, but are missing: %s.' % ', '.join(missing_packages))

        log_file = filesnpaths.get_temp_file_path()

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

