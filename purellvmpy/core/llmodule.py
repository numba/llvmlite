from __future__ import print_function, absolute_import
from purellvmpy.core import _utils


class Module(object):
    def __init__(self, name=''):
        self.name = name   # name is for debugging/informational
        self.globals = {}
        self.name_manager = _utils.NameManager()

    def add_global(self, globalvalue):
        assert globalvalue.name not in self.globals
        self.globals[globalvalue.name] = globalvalue

    def get_unique_name(self, name=''):
        return self.name_manager.deduplicate(name)

    def __repr__(self):
        body = '\n'.join(str(v) for v in self.globals.values())
        return ('; Module \"%s\"\n\n' % self.name) + body
