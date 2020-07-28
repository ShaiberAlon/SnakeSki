#!/usr/bin/env python

from snakeski.workflows import WorkflowSuperClass
import argparse

w = WorkflowSuperClass(argparse.Namespace(config_file='sandbox/config.json'))
w.init('bla')
