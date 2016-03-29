from __future__ import print_function, absolute_import
from . import context, values, types, _utils


class Module(object):
    def __init__(self, name='', context=context.global_context):
        self.context = context
        self.name = name   # name is for debugging/informational
        self.globals = {}
        self.metadata = []
        self._metadatacache = {}
        self.data_layout = ""
        self.namedmetadata = {}
        self.scope = _utils.NameScope()
        self.triple = 'unknown-unknown-unknown'
        self._sequence = []

    def add_metadata(self, operands):
        """
        Add an unnamed metadata to the module with the given *operands*
        (a list of values) or return a previous equivalent metadata.
        A MDValue instance is returned, it can then be associated to
        e.g. an instruction.
        """
        n = len(self.metadata)
        key = tuple(operands)
        if key not in self._metadatacache:
            md = values.MDValue(self, operands, name=str(n))
            self._metadatacache[key] = md
        else:
            md = self._metadatacache[key]
        return md

    def add_named_metadata(self, name):
        nmd = values.NamedMetaData(self)
        self.namedmetadata[name] = nmd
        return nmd

    def get_named_metadata(self, name):
        return self.namedmetadata[name]

    @property
    def functions(self):
        """
        A list of functions declared or defined in this module.
        """
        return [v for v in self.globals.values()
                if isinstance(v, values.Function)]

    @property
    def global_values(self):
        """
        An iterable of global values in this module.
        """
        return self.globals.values()

    def get_global(self, name):
        """
        Get a global value by name.
        """
        return self.globals.get(name)

    def add_global(self, globalvalue):
        """
        Add a new global value.
        """
        assert globalvalue.name not in self.globals
        self.globals[globalvalue.name] = globalvalue
        self._sequence.append(globalvalue.name)

    def get_unique_name(self, name=''):
        """
        Get a unique global name with the following *name* hint.
        """
        return self.scope.deduplicate(name)

    def declare_intrinsic(self, intrinsic, tys=(), fnty=None):
        def _error():
            raise NotImplementedError("unknown intrinsic %r with %d types"
                                      % (intrinsic, len(tys)))

        name = '.'.join([intrinsic] + [t.intrinsic_name for t in tys])
        if name in self.globals:
            return self.globals[name]

        if fnty is not None:
            # General case: function type is given
            pass
        # Compute function type if omitted for common cases
        elif len(tys) == 0 and intrinsic == 'llvm.assume':
            fnty = types.FunctionType(types.VoidType(), [types.IntType(1)])
        elif len(tys) == 1:
            if intrinsic == 'llvm.powi':
                fnty = types.FunctionType(tys[0], [tys[0], types.IntType(32)])
            elif intrinsic == 'llvm.pow':
                fnty = types.FunctionType(tys[0], tys*2)
            else:
                fnty = types.FunctionType(tys[0], tys)
        elif len(tys) == 2 and intrinsic == 'llvm.memset':
            tys = [tys[0], types.IntType(8), tys[1],
                   types.IntType(32), types.IntType(1)]
            fnty = types.FunctionType(types.VoidType(), tys)
        elif len(tys) == 3 and intrinsic in ('llvm.memcpy', 'llvm.memmove'):
            tys = tys + [types.IntType(32), types.IntType(1)]
            fnty = types.FunctionType(types.VoidType(), tys)
        else:
            _error()
        return values.Function(self, fnty, name=name)

    def get_identified_types(self):
        return self.context.identified_types

    def _get_metadata_lines(self):
        mdbuf = []
        for k, v in self.namedmetadata.items():
            mdbuf.append("!{name} = !{{ {operands} }}".format(
                name=k, operands=','.join(i.get_reference()
                                          for i in v.operands)))
        for md in self.metadata:
            mdbuf.append(str(md))
        return mdbuf

    def _stringify_metadata(self):
        # For testing
        return "\n".join(self._get_metadata_lines())

    def __repr__(self):
        lines = []
        # Header
        lines += [
            '; ModuleID = "%s"' % (self.name,),
            'target triple = "%s"' % (self.triple,),
            'target datalayout = "%s"' % (self.data_layout,),
            '']
        # Type declarations
        lines += [it.get_declaration()
                  for it in self.get_identified_types().values()]
        # Body
        lines += [str(self.globals[k]) for k in self._sequence]
        # Metadata
        lines += self._get_metadata_lines()

        return "\n".join(lines)
