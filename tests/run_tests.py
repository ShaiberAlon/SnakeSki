#!/usr/bin/env python

import os
import argparse
import snakeski.workflows as w
from snakeski.workflows import WorkflowSuperClass

os.makedirs('sandbox/test-output', exist_ok = True)
s = w.SnakefileGenerator(argparse.Namespace(config_file = 'sandbox/c.json', name = 't', output_dir = 'sandbox/test-output'))

W = WorkflowSuperClass(argparse.Namespace(config_file='sandbox/config.json'))
W.init('bla')

#s = w.SnakefileGenerator(argparse.Namespace(config_file = 'sandbox/config.json', name = 't', output_dir = 'sandbox/test-output'))
