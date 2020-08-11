# -*- coding: utf-8

import os
import argparse

import snakeski.workflows as w
from snakeski.workflows import WorkflowSuperClass


workflow_object = WorkflowSuperClass(argparse.Namespace(config=config))
workflow_object.init('{name}')

rule {name}_target_rule:
    input: workflow_object.target_files


for _subworkflow in workflow_object.tasks:
    _include = os.path.join(os.path.dirname(__file__),
                          _subworkflow,
                          'Snakefile')
    include: _include
