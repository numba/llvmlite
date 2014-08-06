from llvmlite import binding as llvm

# Initialize native target
llvm.initialize_native_target()


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
        return TargetMachine()

    def create(self, tm):
        return llvm.create_jit_compiler(self.module, opt=self._opt)


class TargetMachine(object):
    def __init__(self):
        self.triple = llvm.get_default_triple()



