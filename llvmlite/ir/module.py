from __future__ import print_function, absolute_import
from . import context, values


class Module(object):
    def __init__(self, name='', context=context.global_context):
        self.context = context
        self.name = name   # name is for debugging/informational
        self.globals = {}
        self.metadata = []
        self.namedmetadata = {}
        self.scope = context.scope.get_child()
        self.triple = 'unknown-unknown-unknown'
        self._sequence = []

    @property
    def functions(self):
        return [v for v in self.globals.values()
                if isinstance(v, values.Function)]

    @property
    def global_variables(self):
        return self.globals.values()


    def add_global(self, globalvalue):
        """Add a global value
        """
        assert globalvalue.name not in self.globals
        self.globals[globalvalue.name] = globalvalue
        self._sequence.append(globalvalue.name)

    def get_unique_name(self, name=''):
        """Util for getting a unique name.
        """
        return self.name_manager.deduplicate(name)

    def __repr__(self):
        body = '\n'.join(str(self.globals[k]) for k in self._sequence)
        fmt = ('; ModuleID = "{name}"\n'
               'target triple = "{triple}"\n\n'
               '{body}')
        return fmt.format(name=self.name, triple=self.triple, body=body)
