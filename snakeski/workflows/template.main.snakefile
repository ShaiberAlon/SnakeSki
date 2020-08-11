# -*- coding: utf-8

import os
import argparse

import snakeski.workflows as w
from snakeski.workflows import WorkflowSuperClass


workflow_object = WorkflowSuperClass(argparse.Namespace(config=config))
workflow_object.init('{name}')

rule {name}_target_rule:
    input: workflow_object.target_files

{include_cmd}
