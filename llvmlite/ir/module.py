from __future__ import print_function, absolute_import
from . import context, values, types


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

    def add_metadata(self, operands):
        n = len(self.metadata)
        return values.MetaData(self, operands, name=str(n))

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
        return self.scope.deduplicate(name)

    def declare_intrinsic(self, intrinsic, tys):
        name = '.'.join([intrinsic, '.'.join(t.intrinsic_name for t in tys)])
        if name in self.globals:
            return self.globals[name]
        else:
            if len(tys) == 1:
                if intrinsic == 'llvm.powi':
                    fnty = types.FunctionType(tys[0], [tys[0],
                                                       types.IntType(32)])
                elif intrinsic == 'llvm.pow':
                    fnty = types.FunctionType(tys[0], tys*2)
                else:
                    fnty = types.FunctionType(tys[0], tys)
            else:
                raise NotImplementedError(name)
            return values.Function(self, fnty, name=name)

    def __repr__(self):
        body = '\n'.join(str(self.globals[k]) for k in self._sequence)
        fmt = ('; ModuleID = "{name}"\n'
               'target triple = "{triple}"\n\n'
               '{body}')
        return fmt.format(name=self.name, triple=self.triple, body=body)
