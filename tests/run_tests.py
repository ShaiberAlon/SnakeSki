#!/usr/bin/env python

import os
import argparse
import snakeski.workflows as w
from snakeski.workflows import WorkflowSuperClass

os.makedirs('sandbox/test-output', exist_ok = True)

W = WorkflowSuperClass(argparse.Namespace(config_file='sandbox/config.json'))
W.init('bla')

s = w.SnakefileGenerator(argparse.Namespace(config_file = 'sandbox/config.json', name = 'hg19', output_dir = 'sandbox/test-output/hg19'))
