#!/usr/bin/env python

from snakeski.workflows import WorkflowSuperClass
import snakeski.workflows as w
import argparse

W = WorkflowSuperClass(argparse.Namespace(config_file='sandbox/config.json'))
W.init('bla')

s = w.SnakefileGenerator(argparse.Namespace(config_file = 'sandbox/config.json', name = 't', output_dir = '/Users/alonshaiber/Downloads/SNAKE'))
