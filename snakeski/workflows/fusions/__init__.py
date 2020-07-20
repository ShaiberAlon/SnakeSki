# -*- coding: utf-8
# pylint: disable=line-too-long
"""
    Classes to define and work with fusions workflow
"""

import os
import snakeski
from snakeski.workflows import WorkflowSuperClass

__author__ = "Alon Shaiber"
__credits__ = ["Adopted partly from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__version__ = snakeski.__version__
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


class FusionsWorkflow(WorkflowSuperClass):
    def __init__(self, args=None):
        workflow_name = 'fusions'
        self.init_workflow_super_class(args, workflow_name=workflow_name)

        # TODO: these will be modified to match the expected outputs of the 
        # workflows that generate them
        param_dict = {'jabba': ''}
        param_dict = {'gencode': ''}
        param_dict = {'id': ''}

        self.dirs_dict.update({"FUSIONS_DIR": "Fusions"})

        targets = [os.path.join(self.ROOT_DIR,
                                self.dirs_dict["FUSIONS_DIR"],
                                pair,
                                "fusions.rds") for pair in self.pairs.index]

        self.target_files.extend(targets)
