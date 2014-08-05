from __future__ import print_function, absolute_import
from . import context


class Module(object):
    def __init__(self, name='', context=context.global_context):
        self.context = context
        self.name = name   # name is for debugging/informational
        self.globals = {}
        self.metadata = []
        self.namedmetadata = {}
        self.scope = context.scope.get_child()
        self.triple = 'unknown-unknown-unknown'

    def add_global(self, globalvalue):
        """Add a global value
        """
        assert globalvalue.name not in self.globals
        self.globals[globalvalue.name] = globalvalue

    def get_unique_name(self, name=''):
        """Util for getting a unique name.
        """
        return self.name_manager.deduplicate(name)

    def __repr__(self):
        body = '\n'.join(str(v) for v in self.globals.values())
        fmt = ('; ModuleID = "{name}"\n'
               'target triple = "{triple}"\n\n'
               '{body}')
        return fmt.format(name=self.name, triple=self.triple, body=body)
