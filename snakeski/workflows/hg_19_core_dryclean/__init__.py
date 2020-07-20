
# -*- coding: utf-8
# pylint: disable=line-too-long
"""
    Classes to define and work with hg 19 core dryclean workflow
"""

import snakeski
from snakeski.workflows import WorkflowSuperClass

__author__ = "Alon Shaiber"
__credits__ = ["Adopted partly from the anvi'o project (https://github.com/merenlab/anvio)."]
__license__ = "GPL 3.0"
__version__ = snakeski.__version__
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


class hg19CoreDrycleanWorkflow(WorkflowSuperClass):
    def __init__(self, args=None):
        workflow_name = 'hg19_core_dryclean'
        self.init_workflow_super_class(args, workflow_name=workflow_name)

        self.dirs_dict.update({"ONCOTABLE_DIR": "Oncotable",
                               "FUSIONS_DIR": "Fusions"})

        targets = []
        targets.extend([os.path.join(self.ROOT_DIR,
                                self.dirs_dict["ONCOTABLE_DIR"],
                                pair,
                                "oncotable.rds") for pair in self.pairs.index])

        targets.extend([os.path.join(self.ROOT_DIR,
                           self.dirs_dict["FUSIONS_DIR"],
                           pair,
                           "fusions.rds") for pair in self.pairs.index])

        self.target_files = targets
