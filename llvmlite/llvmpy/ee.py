from llvmlite import binding as llvm

RELOC_PIC = 'pic'

# Initialize native target
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


def dylib_add_symbol(name, addr):
    llvm.add_symbol(name, addr)


def dylib_address_of_symbol(name):
    llvm.address_of_symbol(name)


class EngineBuilder(object):
    @classmethod
    def new(cls, mod):
        return EngineBuilder(mod)

    def __init__(self, mod):
        self.module = llvm.parse_assembly(str(mod))
        self._opt = 2
        self._mattrs = ''

    def opt(self, opt):
        self._opt = opt
        return self

    def mattrs(self, attrs):
        self._mattrs = attrs
        return self

    def select_target(self):
        # TODO
        return TargetMachine()

    def create(self, tm):
        return llvm.create_mcjit_compiler(self.module, tm._tm)


class TargetMachine(object):
    def __init__(self, cpu='', features='', opt=2, reloc='default',
                 codemodel='jitdefault'):
        self.triple = llvm.get_default_triple()
        self.target = llvm.Target.from_triple(self.triple)
        self._tm = self.target.create_target_machine(self.triple, cpu,
                                                     features, opt, reloc,
                                                     codemodel)

    @staticmethod
    def new(*args, **kwargs):
        return TargetMachine(*args, **kwargs)

    def emit_object(self, module):
        return self._tm.emit_object(module)

    def emit_assembly(self, module):
        return self._tm.emit_assembly(module)
