# -*- coding: utf-8
# pylint: disable=line-too-long
"""File/Path operations mostly adopted from https://github.com/merenlab/anvio"""

import os
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

