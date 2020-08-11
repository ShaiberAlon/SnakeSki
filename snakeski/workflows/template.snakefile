# -*- coding: utf-8

import os
import argparse

import snakeski.workflows as w
from snakeski.workflows import WorkflowSuperClass



sub_workflow_mode = False if '{task}/Snakefile' in workflow.included[0] else True
if not sub_workflow_mode:
    # if this is not a sub workflow then we need to initialize the workflow object
    # don't be confused, child. when things come to this point, the variable `config`
    # is already magically filled in by snakemake:
    {task}_workflow_object = WorkflowSuperClass(argparse.Namespace(config=config))
    {task}_workflow_object.init('{task}')

    rule {task}_target_rule:
        input: {task}_workflow_object.target_files

else:
    {task}_workflow_object = workflow_object

dirs_dict = {task}_workflow_object.dirs_dict


rule {task}:
    version: 1.0
    log: os.path.abspath(os.path.join(dirs_dict["LOGS_DIR"], "{wildcard}-{task}.log"))
    input:
{inputs}
    output:
{outputs}
    params:
{task_params}
        output_dir = os.path.join({task}_workflow_object.ROOT_DIR, dirs_dict['{task}'], '{wildcard}'),
        module_path = {task}_workflow_object.modules['{task}']
    threads: {task}_workflow_object.T('{task}')
    resources: nodes = {task}_workflow_object.T('{task}')
    shell:
        """
        # go to the directory
        mkdir -p {{params.output_dir}}
        cd {{params.output_dir}}

        # run
        {run_cmd}

        # go back
        cd -
        """
