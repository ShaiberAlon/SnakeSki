
import os
import json
import argparse
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
            return os.path.realpath(os.path.join(self.ROOT_DIR, task, '{pair}', output_name_fixed))
        return None


    def get_tasks_dict(self):
        ''' Returns the task dictionary by reading the config file.

        The input in the config file could be either:
          1. A list of paths to task files.
          2. A single task file.
          3. a path to a directory.
        An empty dictionary is returned by default.
        '''

        tasks = {}
        task_list = self.config.get('tasks', [])

        if type(task_list) is not list:
            if type(task_list) is not str:
                raise ConfigError('"tasks" must be provided as a list or as a \
                                   single string in the config file, but you \
                                   provided a "%s"' % type(task_list))
            # check if directory
            if os.path.isdir(task_list):
                # get all the *.task files from the directory
                import glob
                task_list = glob.glob(os.path.join(task_list, '*.task'))
            else:
                # a single path was provided so let's convert to list
                task_list = [task_list]

        task_file_with_bad_suffix = [t for t in task_list if not t.endswith('.task')]
        if task_file_with_bad_suffix:
            raise ConfigError('Task files must have suffix ".task", but some of \
                               the task files you provided don\'t. For example: \
                               %s' % task_file_with_bad_suffix[0])

        for t in task_list:
            # make sure task file exist
            filesnpaths.is_file_exists(t)

        tasks = dict([(utils.fix_name(os.path.basename(t)[:-5]), t) for t in task_list])

        return(tasks)


    def add_task_definitions(self, workflow_name):
        ''' Iterate through tasks to populate input and output definitions and module paths'''

        if not self.tasks:
            raise ConfigError('You must include at least one task in your config file.')

        for task in self.tasks:
            self.read_task_file(task)

        #self.check_input_params()
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
                    if False:
                        print('Warning: the parameter %s in task %s matches an output \
                               parameter of task %s, and yet a default was provided in \
                               %s. The default value will be ignored and the matching output \
                               will be used. If you don\'t wish for this output to be used \
                               and wish to use the default value, then we suggest that you \
                               change the name of the column that this particular input parameter \
                               is pointint at. Feel free to contact us if you are confused, this is \
                               indeed a confusing situation.' % (iparam, input_task, output_task, input_task))

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

        param_dataframe.index = [s.replace('.', '_') for s in param_dataframe.index]

        # make sure that all input params are of "param_type" path or value
        bad_params = [p for p in param_dataframe.loc[param_dataframe['io_type'] == 'input'].index if param_dataframe.loc[p, 'param_type'] not in ['path', 'value']]
        if bad_params:
            raise ConfigError('Input parameters must be defined as either "path" \
                               or "value", but your task file "%s" declares the \
                               param "%s" as "%s"' % (task_file, bad_params[0], param_dataframe.loc[bad_params[0], 'param_type']))

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


class SnakefileGenerator():
    '''Class to generate Snakefiles using task files.'''
    def __init__(self, args):
        A = lambda x: self.args.__dict__[x] if x in self.args.__dict__ else None

        self.args = args
        self.config = A('config')
        self.config_file = A('config_file')
        self.name = A('name')
        self.output_dir = A('output_dir')
        self.W = WorkflowSuperClass(argparse.Namespace(config_file=self.config_file))
        self.W.init(self.name)

        # in the future we might turn this to a list of wildcards
        wildcard = '{pair}'

        if os.path.isdir(self.output_dir):
            raise ConfigError('There is already an output directory %s. We don\'t \
                               like overwriting stuff.' % self.output_dir)
        # get the template
        with open(get_path_to_snakefile_template()) as f:
            template = f.read()

        allparams = {}
        for task in self.W.param_dataframes:
            d = self.W.param_dataframes[task]
            params = []
            for param in d.loc[(d['io_type'] == 'input') & (d['param_type'] == 'value')].index:
                # iterate through non-file inputs (AKA params)
                params.append(get_snakefile_param_definition(task, param))
            param_str = ',\n'.join(params)
            param_str = param_str + ','

            inputs = []
            for param in d.loc[(d['io_type'] == 'input') & (d['param_type'] == 'path')].index:
                # iterate through "path" inputs (AKA input files)
                inputs.append(get_snakefile_param_definition(task, param))
            input_str = ',\n'.join(inputs)

            outputs = []
            for param, row in d.loc[d['io_type'] == 'output'].iterrows():
                # iterate through outputs (AKA outputs)
                filename = row['param_name_in_pairs_table']
                filename = utils.fix_output_parameter_name(filename)
                outputs.append(get_snakefile_output_param(task, param, filename))
            output_str = ',\n'.join(outputs)

            run_cmd = self.get_shell_command(task)

            format_dict = {'task': task,
                           'inputs': input_str,
                           'outputs': output_str,
                           'task_params': param_str,
                           'run_cmd': run_cmd,
                           'wildcard': wildcard}

            snakefile = template.format(**format_dict)
            snakefile = snakefile.replace('<libdir>', '{params.module_path}')

            snakefile_dir = os.path.join(self.output_dir, task)
            os.makedirs(snakefile_dir, exist_ok = True)
            snakefile_path = os.path.join(snakefile_dir, 'Snakefile')
            with open(snakefile_path, 'w') as f:
                f.write(snakefile)

        # create the main snakefile
        with open(get_path_to_main_snakefile_template()) as f:
            main_template = f.read()
        main_snakefile = main_template.format(name = self.name, dir = utils.fix_path(self.output_dir))

        snakefile_path = os.path.join(self.output_dir, 'Snakefile')
        print('Writing the main Snakefile for workflow "%s" to: %s' %(self.name, snakefile_path))
        with open(snakefile_path, 'w') as f:
            f.write(main_snakefile)


    def get_param_dict_for_cmdline(self, task):
        '''Return a dictionary to use in a str.format() expression for the cmndline

        The dictionary is of the following format for example:
        cmd_dict = {'jabba_rds': '{input.jabba_rds}',
             'id': '{params.id}'}
        '''
        d = self.W.param_dataframes[task]

        cmd_dict = {}

        value_params = d.loc[(d['io_type'] == 'input') & (d['param_type'] == 'value')].index
        cmd_dict.update(dict([(param, '{params.%s}' % param) for param in value_params]))

        input_params = d.loc[(d['io_type'] == 'input') & (d['param_type'] == 'path')].index
        cmd_dict.update(dict([(param, '{input.%s}' % param) for param in input_params]))

        output_params = d.loc[d['io_type'] == 'output'].iterrows()
        output_params_fixed = [utils.fix_output_parameter_name(row['param_name_in_pairs_table']) for param, row in output_params]
        cmd_dict.update(dict([(param, '{output.%s}' % param) for param in output_params_fixed]))

        return(cmd_dict)


    def get_shell_command(self, task):
        ''' Get the command line from the module file and format it with proper snakemake wildcard notation.'''
        cmd = utils.get_command_from_module(self.W.modules[task])
        param_dict_for_cmdline = self.get_param_dict_for_cmdline(task)
        try:
            cmd = cmd.format(**param_dict_for_cmdline)
        except KeyError as e:
            raise ConfigError('Something went wrong while parsing task file %s. \
                               The following keyword is causing trouble: %s' % (task, e))
        return(cmd)


def get_path_to_snakefile_template():
    base = get_path_to_workflows_dir()
    return(os.path.join(base, 'template.snakefile'))


def get_path_to_main_snakefile_template():
    base = get_path_to_workflows_dir()
    return(os.path.join(base, 'template.main.snakefile'))


def get_snakefile_param_definition(task, param):
    s = "        {param} = lambda wildcards: {task}_workflow_object.get_rule_param('{task}', '{param}', wildcards)"
    s = s.format(param = param, task = task)
    return(s)


def get_path_to_workflows_dir():
    # this returns a path
    base_path = os.path.dirname(__file__)
    return base_path


def D(debug_message, debug_log_file_path=".SNAKEMAKEDEBUG"):
    with open(debug_log_file_path, 'a') as output:
            output.write(str(debug_message) + '\n\n')


def get_snakefile_output_param(task, param, filename, wildcards = 'pair'):
    s = "        {param} = os.path.realpath(os.path.join({task}_workflow_object.ROOT_DIR, dirs_dict['{task}'], '{wildcards}', '{filename}'))"
    if type(wildcards) == list:
        # this is a place holder in case we would want to use multiple wildcards in the future
        # notice that if we go down this road then we would need to also treat the log definition to contain all wildcards
        # as well as change get_rule_param to be compatible with such a change
        wildcards_str = ', '.join(['{%s}' % wildcard for wildcard in wildcards])
    elif type(wildcards) == str:
        wildcards_str = '{%s}' % wildcards
    else:
        raise ConfigError('Wildcards must be either a single string or a list \
                           of strings, but an object of type %s was provided.' % type(wildcards))
    s = s.format(param = param, task = task, filename=filename, wildcards=wildcards_str)
    return(s)
