# -*- coding: utf-8
# pylint: disable=line-too-long
"""
    Some basic definitions
"""

import copy

__version__ = 'v1'

D = {
    'workflow-name': (
            ['-w', '--workflow-name'],
            {'metavar': "NAME",
             'required': True,
             'help': "The name for the SnakeSki workflow."}
                ),
    'config': (
            ['-c', '--config'],
            {'metavar': "CONFIG",
             'required': True,
             'help': "SnakeSki config file."}
                ),
    'output-dir': (
            ['-O', '--output-dir'],
            {'metavar': "PATH",
             'required': True,
             'help': "Output directory. This directory should not exist yet and will be generated."}
                )
    }

# two functions that works with the dictionary above.
def A(param_id, exclude_param=None):
    if exclude_param:
        return [p for p in D[param_id][0] if p != exclude_param]
    else:
        return D[param_id][0]

def K(param_id, params_dict={}):
    kwargs = copy.deepcopy(D[param_id][1])
    for key in params_dict:
        kwargs[key] = params_dict[key]

    return kwargs

