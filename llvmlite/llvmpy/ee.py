from llvmlite import binding as llvm
from collections import defaultdict

RELOC_PIC = 'pic'

# Initialize native target
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


class EngineBuilder(object):
    """Emulate llvm::EngineBuilder.
    """
    @classmethod
    def new(cls, mod):
        return EngineBuilder(mod)

    def __init__(self, mod):
        self.module = llvm.parse_assembly(str(mod))
        self._opt = 2
        self._mattrs = ''
        self._options = defaultdict(bool)
        self._use_mcjit = True

    def opt(self, opt):
        self._opt = opt
        return self

    def mattrs(self, attrs):
        self._mattrs = attrs
        return self

    def use_mcjit(self, enable=True):
        self._use_mcjit = enable
        return self

    def emit_jit_debug(self, enable=True):
        self._options['jitdebug'] = enable
        return self

    def print_machine_code(self, enable=True):
        self._options['printmc'] = enable
        return self

    def select_target(self):
        target = llvm.Target.from_triple(self.module.triple)
        tm = target.create_target_machine(features=self._mattrs,
                                          opt=self._opt, **self._options)
        return TargetMachine(target=target, triple=target.triple, tm=tm)

    def create(self, tm=None):
        if tm is None:
            tm = self.select_target()
        if isinstance(tm, TargetMachine):
            tm = tm._tm
        if self._use_mcjit:
            return llvm.create_mcjit_compiler(self.module, tm)
        else:
            return llvm.create_jit_compiler_with_tm(self.module, tm)


class TargetMachine(object):
    @staticmethod
    def new(cpu='', features='', opt=2, reloc='default',
            codemodel='jitdefault'):
        target = llvm.Target.from_default_triple()
        triple = target.triple
        tm = target.create_target_machine(cpu, features, opt,
                                          reloc, codemodel)
        return TargetMachine(target=target, triple=triple, tm=tm)

    def __init__(self, target, triple, tm):
        self.target = target
        self.triple = triple
        self._tm = tm

    def emit_object(self, module):
        return self._tm.emit_object(module)

    def emit_assembly(self, module):
        return self._tm.emit_assembly(module)

    def add_analysis_passes(self, pm):
        self._tm.add_analysis_passes(pm)

    @property
    def target_data(self):
        return self._tm.target_data
