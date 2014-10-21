from __future__ import print_function, absolute_import
from ctypes import (POINTER, c_char_p, c_ulonglong, c_int, c_size_t,
                    c_void_p, string_at)
from . import ffi, parse_assembly
from .common import _decode_string


def get_default_triple():
    with ffi.OutputString() as out:
        ffi.lib.LLVMPY_GetDefaultTargetTriple(out)
        return str(out)


def create_target_data(strrep):
    return TargetData(ffi.lib.LLVMPY_CreateTargetData(strrep.encode('utf8')))


class TargetData(ffi.ObjectRef):

    def __str__(self):
        with ffi.OutputString() as out:
            ffi.lib.LLVMPY_CopyStringRepOfTargetData(self, out)
            return str(out)

    def _dispose(self):
        ffi.lib.LLVMPY_DisposeTargetData(self)

    def abi_size(self, ty):
        from llvmlite.ir import Type, Module, GlobalVariable

        # XXX unused
        if isinstance(ty, Type):
            # We need to convert our type object to the LLVM's object
            m = Module()
            foo = GlobalVariable(m, ty, name="foo")
            with parse_assembly(str(m)) as mod:
                gv = mod.get_global_variable(foo.name)
                ty = gv.type

        return ffi.lib.LLVMPY_ABISizeOfType(self, ty)


RELOC = frozenset(['default', 'static', 'pic', 'dynamicnopic'])
CODEMODEL = frozenset(['default', 'jitdefault', 'small', 'kernel',
                       'medium', 'large'])


class Target(ffi.ObjectRef):
    _triple = ''

    # No _dispose() method since LLVMGetTargetFromTriple() returns a
    # persistent object.

    @classmethod
    def from_default_triple(cls):
        return cls.from_triple(get_default_triple())

    @classmethod
    def from_triple(cls, triple):
        with ffi.OutputString() as outerr:
            target = ffi.lib.LLVMPY_GetTargetFromTriple(triple.encode('utf8'),
                                                        outerr)
            if not target:
                raise RuntimeError(str(outerr))
            target = cls(target)
            target._triple = triple
            return target

    @property
    def name(self):
        s = ffi.lib.LLVMPY_GetTargetName(self)
        return _decode_string(s)

    @property
    def description(self):
        s = ffi.lib.LLVMPY_GetTargetDescription(self)
        return _decode_string(s)

    def __str__(self):
        return "<Target {0} ({1})>".format(self.name, self.description)

    def create_target_machine(self, triple='', cpu='', features='',
                              opt=1, reloc='default', codemodel='jitdefault'):
        assert 0 <= opt <= 3
        assert reloc in RELOC
        assert codemodel in CODEMODEL
        triple = triple or self._triple
        tm = ffi.lib.LLVMPY_CreateTargetMachine(self,
                                                triple.encode('utf8'),
                                                cpu.encode('utf8'),
                                                features.encode('utf8'),
                                                opt,
                                                reloc.encode('utf8'),
                                                codemodel.encode('utf8'),
                                                )
        if tm:
            return TargetMachine(tm)
        else:
            raise RuntimeError("Cannot create target machine")


class TargetMachine(ffi.ObjectRef):
    def _dispose(self):
        ffi.lib.LLVMPY_DisposeTargetMachine(self)

    def emit_object(self, module):
        """
        Represent the module as a code object, suitable for use with
        the platform's linker.  Returns a byte string.
        """
        return self._emit_to_memory(module, use_object=True)

    def emit_assembly(self, module):
        """
        Return the raw assembler of the module, as a string.

        llvm.initialize_native_asmprinter() must have been called first.
        """
        return _decode_string(self._emit_to_memory(module, use_object=False))

    def _emit_to_memory(self, module, use_object=False):
        """Returns bytes of object code of the module.

        Args
        ----
        use_object : bool
            Emit object code or (if False) emit assembly code.
        """
        with ffi.OutputString() as outerr:
            mb = ffi.lib.LLVMPY_TargetMachineEmitToMemory(self, module,
                                                          int(use_object),
                                                          outerr)
            if not mb:
                raise RuntimeError(str(outerr))

        bufptr = ffi.lib.LLVMPY_GetBufferStart(mb)
        bufsz = ffi.lib.LLVMPY_GetBufferSize(mb)
        try:
            return string_at(bufptr, bufsz)
        finally:
            ffi.lib.LLVMPY_DisposeMemoryBuffer(mb)

# ============================================================================
# FFI

ffi.lib.LLVMPY_GetDefaultTargetTriple.argtypes = [POINTER(c_char_p)]

ffi.lib.LLVMPY_CreateTargetData.argtypes = [c_char_p]
ffi.lib.LLVMPY_CreateTargetData.restype = ffi.LLVMTargetDataRef

ffi.lib.LLVMPY_CopyStringRepOfTargetData.argtypes = [
    ffi.LLVMTargetDataRef,
    POINTER(c_char_p),
]

ffi.lib.LLVMPY_DisposeTargetData.argtypes = [
    ffi.LLVMTargetDataRef,
]

ffi.lib.LLVMPY_AddTargetData.argtypes = [ffi.LLVMTargetDataRef,
                                         ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_ABISizeOfType.argtypes = [ffi.LLVMTargetDataRef,
                                         ffi.LLVMTypeRef]
ffi.lib.LLVMPY_ABISizeOfType.restype = c_ulonglong

ffi.lib.LLVMPY_GetTargetFromTriple.argtypes = [c_char_p, POINTER(c_char_p)]
ffi.lib.LLVMPY_GetTargetFromTriple.restype = ffi.LLVMTargetRef

ffi.lib.LLVMPY_GetTargetName.argtypes = [ffi.LLVMTargetRef]
ffi.lib.LLVMPY_GetTargetName.restype = c_char_p

ffi.lib.LLVMPY_GetTargetDescription.argtypes = [ffi.LLVMTargetRef]
ffi.lib.LLVMPY_GetTargetDescription.restype = c_char_p

ffi.lib.LLVMPY_CreateTargetMachine.argtypes = [
    ffi.LLVMTargetRef,
    # Triple
    c_char_p,
    # CPU
    c_char_p,
    # Features
    c_char_p,
    # OptLevel
    c_int,
    # Reloc
    c_char_p,
    # CodeModel
    c_char_p,
]
ffi.lib.LLVMPY_CreateTargetMachine.restype = ffi.LLVMTargetMachineRef

ffi.lib.LLVMPY_DisposeTargetMachine.argtypes = [ffi.LLVMTargetMachineRef]

ffi.lib.LLVMPY_TargetMachineEmitToMemory.argtypes = [
    ffi.LLVMTargetMachineRef,
    ffi.LLVMModuleRef,
    c_int,
    POINTER(c_char_p),
]
ffi.lib.LLVMPY_TargetMachineEmitToMemory.restype = ffi.LLVMMemoryBufferRef

ffi.lib.LLVMPY_GetBufferStart.argtypes = [ffi.LLVMMemoryBufferRef]
ffi.lib.LLVMPY_GetBufferStart.restype = c_void_p

ffi.lib.LLVMPY_GetBufferSize.argtypes = [ffi.LLVMMemoryBufferRef]
ffi.lib.LLVMPY_GetBufferSize.restype = c_size_t

ffi.lib.LLVMPY_DisposeMemoryBuffer.argtypes = [ffi.LLVMMemoryBufferRef]
