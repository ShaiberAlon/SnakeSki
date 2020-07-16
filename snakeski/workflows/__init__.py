
import os
import json
import pandas as pd
import snakeski.utils as utils
import snakeski.filesnpaths as filesnpaths

from snakeski.errors import ConfigError

class WorkflowSuperClass:
    def __init__(self):
        if 'args' not in self.__dict__:
            raise ConfigError("You need to initialize `WorkflowSuperClass` from within a class that\
                               has a member `self.args`.")

        A = lambda x: self.args.__dict__[x] if x in self.args.__dict__ else None

        self.config = A('config')
        self.threads = {}
        self.target_files = []
        self.pairs = None
        self.task_definitions = {}
        self.modules = {}
        self.dirs_dict = {"LOGS_DIR": "00_LOGS"}
        self.params = {}
        self.subworkflows = []



    def T(self, rule):
        try:
            return self.threads[rule]
        except KeyError:
            return 1


    def init_workflow_super_class(self, args, workflow_name):
        '''
            if a regular instance of workflow object is being generated, we
            expect it to have a parameter `args`. if there is no `args` given, we
            assume the class is being inherited as a base class from within another.

            For a regular instance of a workflow this function will set the args
            and init the WorkflowSuperClass.
        '''
        if args:
            if len(self.__dict__):
                raise ConfigError("Something is wrong. You are ineriting %s from \
                                   within another class, yet you are providing an `args` parameter.\
                                   This is not alright." % type(self))
            self.args = args
            self.name = workflow_name
            WorkflowSuperClass.__init__(self)
        else:
            if not len(self.__dict__):
                raise ConfigError("When you are *not* inheriting %s from within\
                                   a super class, you must provide an `args` parameter." % type(self))
            if 'name' not in self.__dict__:
                raise ConfigError("The super class trying to inherit %s does not\
                                   have a set `self.name`. Which means there may be other things\
                                   wrong with it, hence things will not continue." % type(self))

        if not self.config:
            raise ConfigError('You need to provide a config file to run this workflow.')

        self.load_pairs_table()
        self.config_sanity_checks()
        self.add_task_definitions(workflow_name)
        self.add_task_definitions(workflow_name)
        # if the user did not specify a directory then use current directory and put everything under "Flow" directory
        self.ROOT_DIR = self.config.get('ROOT_DIR', os.path.join(os.getcwd(), "Flow"))



    def load_pairs_table(self):
        pairs_rds = self.config.get('pairs_rds')
        if not pairs_rds:
            raise ConfigError('You must specify a path to a pairs rds file in your config file.')

        if not filesnpaths.is_file_exists(pairs_rds, dont_raise=True):
            raise ConfigError('The pairs rds file path that was provided does not exist: %s' % pairs_rds)

        self.pairs = pd.read_csv(utils.save_pairs_table_as_TAB_delimited(pairs_rds), sep='\t', index_col=0)


    def add_task_definitions(self, workflow_name):
        ''' Populate the task_definitions and module path by reading the task file'''
        task_file = self.config.get(workflow_name, {}).get('task')

        if not task_file:
            default_tasks = utils.get_default_task_file_path()
            if filesnpaths.is_file_exists(default_tasks, dont_raise=True):
                task_files = json.load(open(default_tasks))
                task_file = task_files.get(workflow_name)

        if not task_file:
            raise ConfigError('You must provide a task file.')

        self.task_definitions[workflow_name] = utils.load_param_table_from_task_file(task_file)
        self.modules[workflow_name] = utils.get_module_path_from_task_file(task_file)


    def get_param_name_from_task_file(self, rule, param):
        try:
            return(self.task_definitions.get(rule, pd.DataFrame()).loc[param, 'param_name_in_pairs_table'])
        except KeyError:
            return None


    def config_sanity_checks(self):
        ''' Place holder for sanity checks
        one thing we have to do here is:
        go through parameters of rules and check if there is redundancy with the pairs table
        '''
        pass


    def get_rule_param(self, rule, param, wildcards):
        param_value = ''
        task_file = self.config.get(rule, {}).get('task')

        if task_file:
            if not self.task_definitions.get(rule, {}).get(param):
                # if a task file was provided then we demand consistency
                raise ConfigError('Someone is requesting a parameter that is not \
                                   defined in the task file. Here are the details: \
                                   The parameter %s was requested for %s, but it \
                                   is not listed in the task file: %s' % (param, rule, task_file))

            param_value = self.pairs.loc[wildcards.pair, self.get_param_name_from_task_file(rule, param)]

        else:
            # if there is no task file we assume the name of the column to be "param"
            try:
                param_value = self.pairs.loc[wildcards.pair, param]
            except KeyError:
                # if there is no such column then we move on to get the default value
                pass

        if not param_value:
            # we get the defalut value
            # this guarantees that Snakemake will run the appropriate step to get this input
            param_value = self.params.get(rule, {}).get(param, '')

        return(param_value)


    def get_default_param(self, param):
        try:
            defaults_file = os.environ['SnakeSkiDefaults']
        except KeyError:
            # there shell environment does not include the variable SnakeSkiDefaults
            # hence we cannot know if and where is a file with default values
            return(None)
        # TODO: would be better to change to is_file_empty
        if filesnpaths.is_file_exists(defaults_file):
            defaults = pd.read_csv(defaults_file, sep='\t', header=None, names=['value'], index_col=0)
            try:
                return(defaults.loc[param, 'value'])
            except KeyError:
                # no default is set for this parameter name
                return(None)
        # the defaults file does not exist
        return(None) 


def get_path_to_workflows_dir():
    # this returns a path
    base_path = os.path.dirname(__file__)
    return base_path


def D(debug_message, debug_log_file_path=".SNAKEMAKEDEBUG"):
    with open(debug_log_file_path, 'a') as output:
            output.write(terminal.get_date() + '\n')
            output.write(str(debug_message) + '\n\n')

