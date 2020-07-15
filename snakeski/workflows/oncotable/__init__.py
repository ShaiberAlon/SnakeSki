# -*- coding: utf-8
# pylint: disable=line-too-long
"""
    Classes to define and work with oncotable workflow
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


class OncotableWorkflow(WorkflowSuperClass):
    def __init__(self, args=None):
        workflow_name = 'oncotable'
        self.init_workflow_super_class(args, workflow_name=workflow_name)
        self.add_task_definitions(workflow_name)

        # TODO: these will be modified to match the expected outputs of the 
        # workflows that generate them
        param_dict = {'annotated_bcf': ''}
        param_dict = {'complex': ''}
        param_dict = {'fusions': ''}
        param_dict = {'filter': 'PASS'}
        param_dict = {'jabba': ''}
        param_dict = {'signature_counts': ''}
        param_dict = {'gencode': self.get_default_param('gencode')}
        param_dict = {'annotated_bcf': ''}
        param_dict = self.params.update({workflow_name: param_dict})
