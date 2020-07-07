import os
from snakeski.errors import ConfigError

class WorkflowSuperClass:
    def __init__(self):
        if 'args' not in self.__dict__:
            raise ConfigError("You need to initialize `WorkflowSuperClass` from within a class that\
                               has a member `self.args`.")

        A = lambda x: self.args.__dict__[x] if x in self.args.__dict__ else None

        self.config = A('config')
        self.threads = {}


    def T(self, rule_name):
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

    def load_pairs_table(self):
        pairs_rds = self.config.get('pairs_rds')
        if not os.path.exists(os.path.abspath(file_path)):
            raise ConfigError('The pairs rds file path that provided does not exist: %s' % pairs_rds)

        # load the rds and save it as a txt file


