
import os
import json
import pandas as pd
import snakeski.utils as utils
import snakeski.filesnpaths as filesnpaths

from snakeski.errors import ConfigError, FilesNPathsError

class WorkflowSuperClass:
    def __init__(self, args):
        A = lambda x: self.args.__dict__[x] if x in self.args.__dict__ else None

        self.args = args
        self.config = A('config')
        self.config_file = A('config_file')
        self.threads = {}
        self.target_files = []
        self.input_param_dict = {} # dictionary to connect input parameters to tasks
        self.output_param_dict = {} # dictionary to connect output parameters to tasks
        self.io_dict = {} # dictionary with output parameters and list of tuples of matching inputs with the format (task, input)
        self.param_dataframes = {}
        self.pairs = None
        self.tasks = {}
        self.modules = {}
        self.dirs_dict = {"LOGS_DIR": "00_LOGS"}
        self.params = {}
        self.subworkflows = []

        if not self.config and not self.config_file:
            raise ConfigError('You must provide a path to a config file.')

        if not self.config:
            filesnpaths.is_file_json_formatted(self.config_file)
            self.config = json.load(open(self.config_file))


    def T(self, task):
        try:
            return self.threads[task]
        except KeyError:
            return 1


    def init(self, workflow_name):
        '''
            if a regular instance of workflow object is being generated, we
            expect it to have a parameter `args`. if there is no `args` given, we
            assume the class is being inherited as a base class from within another.

            For a regular instance of a workflow this function will set the args
            and init the WorkflowSuperClass.
        '''
        self.name = workflow_name
        self.ROOT_DIR = self.config.get('ROOT_DIR', os.path.join(os.getcwd(), "Flow"))
        self.load_pairs_table()

        self.tasks = self.get_tasks_dict()

        if not self.config:
            raise ConfigError('You need to provide a config file to run this workflow.')

        self.config_sanity_checks()
        self.add_task_definitions(workflow_name)
        # if the user did not specify a directory then use current directory and put everything under "Flow" directory
        self.populate_dirs_dict()
        os.makedirs(self.dirs_dict['LOGS_DIR'], exist_ok = True)
        os.makedirs(self.ROOT_DIR, exist_ok = True)


    def populate_dirs_dict(self):
        ''' This is a place holder for now in case we will wish to allow users to change these names using the config file'''
        self.dirs_dict.update(dict(zip(list(self.tasks.keys()), list(self.tasks.keys()))))


    def load_pairs_table(self):
        pairs_rds = self.config.get('pairs_rds')
        if not pairs_rds:
            raise ConfigError('You must specify a path to a pairs rds file in your config file.')

        if not filesnpaths.is_file_exists(pairs_rds, dont_raise=True):
            raise ConfigError('The pairs rds file path that was provided does not exist: %s' % pairs_rds)

        self.pairs = pd.read_csv(utils.save_pairs_table_as_TAB_delimited(pairs_rds), sep='\t', index_col=0)


    def get_output_file_path(self, task, param):
        ''' Return the path to an output file.'''
        output_name = self.get_output_name_from_task_file(task, param)
        if output_name:
            output_name_fixed = utils.fix_output_parameter_name(output_name)
            return os.path.join(self.ROOT_DIR, task, '{pair}', output_name_fixed)
        return None


    def get_tasks_dict(self):
        ''' Returns the task dictionary by reading the config file.
        An empty dictionary is returned by default.'''
        tasks = self.config.get('tasks', {})

        try:
            tasks.keys()
        except:
            raise ConfigError('The tasks in the config file must be defined as a dictionary \
                               with task names as keys and task file paths as values, but the \
                               data you provided was of type "%s".' % type(tasks))
        return(tasks)


    def add_task_definitions(self, workflow_name):
        ''' Iterate through tasks to populate input and output definitions and module paths'''

        if not self.tasks:
            raise ConfigError('You must include at least one task in your config file.')

        for task in self.tasks:
            self.read_task_file(task)

        self.check_input_params()
        self.populate_io_dict()
        self.update_defaults_using_output_parameters()
        self.update_targets()


    def populate_io_dict(self):
        ''' Create a dictionary to map from output files to input files that match them'''
        for oparam in self.output_param_dict:
            matches = []
            for task in self.tasks:
                inputs = self.param_dataframes[task].loc[self.param_dataframes[task]['param_name_in_pairs_table'] == oparam].index
                if len(inputs):
                    matches.extend([(task, i) for i in inputs])

            if len(matches):
                self.io_dict[oparam] = matches


    def update_targets(self):
        ''' Populate self.target_files.'''

        # list of tasks that we don't need to schedule since they have dependencies
        non_target_tasks = [self.output_param_dict[i] for i in self.io_dict]

        target_tasks = set(self.tasks.keys()) - set(non_target_tasks)

        # Iterate over target tasks and add their outputs as targets
        for task in target_tasks:
            task_outputs = self.param_dataframes[task].loc[self.param_dataframes[task]['io_type'] == 'output'].index
            self.target_files.extend([self.get_output_file_path(task, param).format(pair=p) for param in task_outputs for p in self.pairs.index])


    def update_defaults_using_output_parameters(self):
        ''' Find input and output parameters with matching names and use the
        output parameter as the default for the input parameter.
        '''
        for oparam in self.io_dict:
            output_task = self.output_param_dict[oparam]
            for input_task, iparam in self.io_dict[oparam]:
                output_value = self.get_output_file_path(output_task, oparam)
                current_default_value = self.param_dataframes[input_task].loc[iparam, 'default_value']
                if not pd.isna(current_default_value):
                    print('Warning: the parameter %s in task %s matches an output \
                           parameter of task %s, and yet a default was provided in \
                           %s and hence the default from the task file will be used \
                           instead of the output of %s.' % input_task)

                else:
                    self.param_dataframes[input_task].loc[iparam, 'default_value'] = output_value


    def check_input_params(self):
        ''' check if two tasks have the same input parameter pointed to different columns'''
        for iparam in self.input_param_dict:
            if len(self.input_param_dict[iparam]) > 1:
                task_iter = iter(self.input_param_dict[iparam])
                task1 = next(task_iter)
                column_name1 = self.param_dataframes[task1].loc[iparam, 'param_name_in_pairs_table']
                mismatch = [(t, self.param_dataframes[t].loc[iparam, 'param_name_in_pairs_table']) for t in task_iter if self.param_dataframes[t].loc[iparam, 'param_name_in_pairs_table'] != column_name1]
                if mismatch:
                    raise ConfigError('Task files with the same parameters must \
                                       also point to the same column in the pairs \
                                       table, yet there are two or more tasks \
                                       with identical parameters that point to \
                                       different columns in the pairs table. For \
                                       example: the input parameter %s is found in \
                                       tasks %s, %s, but pointing to columns %s, %s, \
                                       respectively.' % (iparam, task1, mismatch[0][0], column_name1, mismatch[0][1]))


        # use output parameters to define populate defaults for input parameters
    def read_task_file(self, task):
        ''' Populate the param_dataframes, input_param_dict, output_param_dict, and module path by reading the task file'''
        task_file = self.tasks.get(task)

        if not task_file:
            raise ConfigError('No task file was provided for task "%s" in your config file.' % task)

        try:
            filesnpaths.is_file_exists(task_file)
        except FilesNPathsError:
            raise ConfigError('The task file "%s" does not exist, and yet it was \
                               provided for task "%s" in your config file' % (task_file, task))

        # read the entire parameter table from the task file
        param_dataframe = utils.load_param_table_from_task_file(task_file)

        for iparam in param_dataframe.loc[(param_dataframe['io_type'] == 'input') & (param_dataframe['param_type'] == 'path')].index:
            # check for literals and store them as defaults
            if utils.is_param_a_literal(param_dataframe.loc[iparam, 'param_name_in_pairs_table']):
                # store the literal as the default value
                param_dataframe.loc[iparam, 'default_value'] = param_dataframe.loc[iparam, 'param_name_in_pairs_table']
                # remove the value from the param_name_in_pairs_table column (since we dont expect such a column to exist
                param_dataframe.loc[iparam, 'param_name_in_pairs_table'] = None

            # populate param dict
            if self.input_param_dict.get(iparam):
                # such a parameter already was defined
                # append this task name
                self.input_param_dict[iparam].append(task)
            else:
                self.input_param_dict[iparam] = [task]

        self.param_dataframes[task] = param_dataframe
        
        for oparam in param_dataframe.loc[param_dataframe['io_type'] == 'output'].index:
            # populate param dict
            if self.output_param_dict.get(oparam):
                # such a parameter already was defined
                # in the future we might allow this, but for now we will raise an error
                raise ConfigError('An output parameter can only be defined once \
                                   for a single task, yet two of your task files \
                                   ("%s" and "%s") define the same output: "%s"\
                                   ' % (task, self.output_param_dict[oparam], oparam))
            else:
                self.output_param_dict[oparam] = task


        # get the module dir path
        self.modules[task] = utils.get_module_path_from_task_file(task_file)


    def get_param_name_from_task_file(self, task, param):
        try:
            return(self.param_dataframes.get(task, pd.DataFrame()).loc[param, 'param_name_in_pairs_table'])
        except KeyError:
            return None


    def get_output_name_from_task_file(self, task, param):
        ''' Get the name of the output from the task file'''
        return self.param_dataframes[task].loc[param, 'param_name_in_pairs_table']

        
    def get_param_type_from_task_file(self, task, param):
        try:
            return(self.param_dataframes.get(task, pd.DataFrame()).loc[param, 'param_type'])
        except KeyError:
            return None


    def get_default_value_from_task_file(self, task, param):
        try:
            return(self.param_dataframes.get(task, pd.DataFrame()).loc[param, 'default_value'])
        except KeyError:
            return None


    def config_sanity_checks(self):
        ''' Place holder for sanity checks
        one thing we have to do here is:
        go through parameters of tasks and check if there is redundancy with the pairs table
        '''
        pass


    def get_rule_param(self, task, param, wildcards):
        param_value = ''

        if param not in self.param_dataframes[task].index:
            task_file = self.tasks[task]
            raise ConfigError('Someone is requesting a parameter that is not \
                               defined in the task file. Here are the details: \
                               The parameter %s was requested for %s, but it \
                               is not listed in the task file: %s' % (param, task, task_file))

        param_column_name = self.get_param_name_from_task_file(task, param)
        if utils.is_param_a_literal(param_column_name):
            # if it is a literal then we simply return the literal value
            param_value = param_column_name

        elif param_column_name in self.pairs.columns:
            # if there is such a column already in the pairs table then we read the value from there
            param_value = self.pairs.loc[wildcards.pair, param_column_name]
            if pd.isna(param_value):
                param_value = ''
        elif param_column_name == self.pairs.index.name:
            # the parameter is the key parameter (usually "pair")
            param_value = wildcards.pair

        if not param_value:
            # get the default value from the task file
            param_value = self.get_default_value_from_task_file(task, param)

        if not param_value:
            if param not in self.output_param_dict:
                raise ConfigError('The following parameter is missing: "%s" from \
                                   the pairs table for the pair id: "%s". you must \
                                   either populate the pairs table or provide a \
                                   default value in the %s task file.' % (param, wildcards.pair, task))

        if param_value and (self.get_param_type_from_task_file(task, param) == 'path'):
            param_value = utils.fix_path(param_value)

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
            output.write(str(debug_message) + '\n\n')

