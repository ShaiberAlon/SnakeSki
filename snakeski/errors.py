# -*- coding: utf-8
# pylint: disable=line-too-long

"""Exceptions"""

import sys
import textwrap
import traceback

from snakeski.ttycolors import color_text


__author__ = "Alon Shaiber"
__credits__ = ["Adopted almost entirely from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


def remove_spaces(text):
    while True:
        if text.find("  ") > -1:
            text = text.replace("  ", " ")
        else:
            break

    return text


class SkiError(Exception, object):
    def __init__(self, e=None):
        Exception.__init__(self)
        return

    def __str__(self):
        max_len = max([len(l) for l in textwrap.fill(self.e, 80).split('\n')])
        error_lines = ['%s%s' % (l, ' ' * (max_len - len(l))) for l in textwrap.fill(self.e, 80).split('\n')]

        error_message = ['%s: %s' % (color_text(self.error_type, 'red'), error_lines[0])]
        for error_line in error_lines[1:]:
            error_message.append('%s%s' % (' ' * (len(self.error_type) + 2), error_line))

        return '\n\n' + '\n'.join(error_message) + '\n\n'


    def clear_text(self):
        return '%s: %s' % (self.error_type, self.e)


class ConfigError(SkiError):
    def __init__(self, e=None):
        self.e = remove_spaces(e)
        self.error_type = 'Config Error'
        SkiError.__init__(self)


