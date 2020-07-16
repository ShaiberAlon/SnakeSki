# -*- coding: utf-8
# pylint: disable=line-too-long
"""File/Path operations mostly adopted from https://github.com/merenlab/anvio"""

import os
import json
import tempfile

from snakeski.errors import FilesNPathsError

__author__ = "Alon Shaiber"
__credits__ = ["Adopted almost entirely from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"

def is_file_exists(file_path, dont_raise=False):
    if not file_path:
        raise FilesNPathsError("No input file is declared...")
    if not os.path.exists(os.path.abspath(file_path)):
        if dont_raise:
            return False
        else:
            raise FilesNPathsError("No such file: '%s' :/" % file_path)
    return True


def get_temp_file_path(prefix=None):
    f = tempfile.NamedTemporaryFile(delete=False, prefix=prefix)
    temp_file_name = f.name
    f.close()
    return temp_file_name


def is_output_file_writable(file_path, ok_if_exists=True):
    if not file_path:
        raise FilesNPathsError("No output file is declared...")
    if not os.access(os.path.dirname(os.path.abspath(file_path)), os.W_OK):
        raise FilesNPathsError("You do not have permission to generate the output file '%s'" % file_path)
    if os.path.exists(file_path) and not ok_if_exists:
        raise FilesNPathsError("The file, '%s', already exists. We don't like overwriting stuff." % file_path)
    return True


def is_file_json_formatted(file_path):
    is_file_exists(file_path)

    try:
        json.load(open(file_path, 'rU'))
    except ValueError as e:
        raise FilesNPathsError("File '%s' does not seem to be a properly formatted JSON\
                file (this is what the json library is complaining about:'%s')." % (file_path, e))

    return True
