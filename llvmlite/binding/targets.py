from __future__ import print_function, absolute_import

import collections
import os
from ctypes import (POINTER, c_char_p, c_longlong, c_int, c_size_t,
                    c_void_p, string_at, byref)

from . import ffi
from .module import parse_assembly
from .common import _decode_string, _encode_string


def get_default_triple():
    """
    Return the default target triple LLVM is configured to produce code for.
    """
    with ffi.OutputString() as out:
        ffi.lib.LLVMPY_GetDefaultTargetTriple(out)
        return str(out)

def get_host_cpu_name():
    """
    Get the name of the host's CPU, suitable for using with
    :meth:`Target.create_target_machine()`.
    """
    with ffi.OutputString() as out:
        ffi.lib.LLVMPY_GetHostCPUName(out)
        return str(out)

def create_target_data(strrep):
    return TargetData(ffi.lib.LLVMPY_CreateTargetData(_encode_string(strrep)))


class TargetData(ffi.ObjectRef):
    """
    A TargetData provides structured access to a data layout.
    Use :func:`create_target_data` to create instances.
    """

    def __str__(self):
        if self._closed:
            return "<dead TargetData>"
        with ffi.OutputString() as out:
            ffi.lib.LLVMPY_CopyStringRepOfTargetData(self, out)
            return str(out)

    def _dispose(self):
        self._capi.LLVMPY_DisposeTargetData(self)

    def get_abi_size(self, ty):
        """
        Get ABI size of LLVM type *ty*.
        """
        return ffi.lib.LLVMPY_ABISizeOfType(self, ty)

    def get_pointee_abi_size(self, ty):
        """
        Get ABI size of pointee type of LLVM pointer type *ty*.
        """
        size = ffi.lib.LLVMPY_ABISizeOfElementType(self, ty)
        if size == -1:
            raise RuntimeError("Not a pointer type: %s" % (ty,))
        return size

    def get_pointee_abi_alignment(self, ty):
        """
        Get minimum ABI alignment of pointee type of LLVM pointer type *ty*.
        """
        size = ffi.lib.LLVMPY_ABIAlignmentOfElementType(self, ty)
        if size == -1:
            raise RuntimeError("Not a pointer type: %s" % (ty,))
        return size

    def add_pass(self, pm):
        """
        Add a DataLayout pass to PassManager *pm*.
        """
        ffi.lib.LLVMPY_AddTargetData(self, pm)
        # Once added to a PassManager, we can never get it back.
        self._owned = True


RELOC = frozenset(['default', 'static', 'pic', 'dynamicnopic'])
CODEMODEL = frozenset(['default', 'jitdefault', 'small', 'kernel',
                       'medium', 'large'])


class Target(ffi.ObjectRef):
    _triple = ''

    # No _dispose() method since LLVMGetTargetFromTriple() returns a
    # persistent object.

    @classmethod
    def from_default_triple(cls):
        triple = get_default_triple()
        # For MCJIT under Windows, see http://lists.cs.uiuc.edu/pipermail/llvmdev/2013-December/068381.html
        if os.name == 'nt':
            triple += '-elf'
        return cls.from_triple(triple)

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

    @property
    def triple(self):
        return self._triple

    def __str__(self):
        return "<Target {0} ({1})>".format(self.name, self.description)

    def create_target_machine(self, cpu='', features='',
                              opt=2, reloc='default', codemodel='jitdefault',
                              jitdebug=False, printmc=False):
        assert 0 <= opt <= 3
        assert reloc in RELOC
        assert codemodel in CODEMODEL
        tm = ffi.lib.LLVMPY_CreateTargetMachine(self,
                                                _encode_string(self._triple),
                                                _encode_string(cpu),
                                                _encode_string(features),
                                                opt,
                                                _encode_string(reloc),
                                                _encode_string(codemodel),
                                                int(jitdebug),
                                                int(printmc),
        )
        if tm:
            return TargetMachine(tm)
        else:
            raise RuntimeError("Cannot create target machine")


class TargetMachine(ffi.ObjectRef):

    def _dispose(self):
        self._capi.LLVMPY_DisposeTargetMachine(self)

    def add_analysis_passes(self, pm):
        """
        Register analysis passes for this target machine with a pass manager.
        """
        ffi.lib.LLVMPY_AddAnalysisPasses(self, pm)

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

    @property
    def target_data(self):
        td = TargetData(ffi.lib.LLVMPY_GetTargetMachineData(self))
        td._owned = True
        return td


def create_target_library_info(triple):
    return TargetLibraryInfo(
        ffi.lib.LLVMPY_CreateTargetLibraryInfo(_encode_string(triple, ))
    )


class TargetLibraryInfo(ffi.ObjectRef):
    """
    A LLVM TargetLibraryInfo.  Use :func:`create_target_library_info`
    to create instances.
    """

    def _dispose(self):
        self._capi.LLVMPY_DisposeTargetLibraryInfo(self)

    def add_pass(self, pm):
        """
        Add this library info as a pass to PassManager *pm*.
        """
        ffi.lib.LLVMPY_AddTargetLibraryInfo(self, pm)
        # Once added to a PassManager, we can never get it back.
        self._owned = True

    def disable_all(self):
        """
        Disable all "builtin" functions.
        """
        ffi.lib.LLVMPY_DisableAllBuiltins(self)

    def get_libfunc(self, name):
        """
        Get the library function *name*.  NameError is raised if not found.
        """
        lf = c_int()
        if not ffi.lib.LLVMPY_GetLibFunc(self, _encode_string(name),
                                         byref(lf)):
            raise NameError("LibFunc '{name}' not found".format(name=name))
        return LibFunc(name=name, identity=lf.value)

    def set_unavailable(self, libfunc):
        """
        Mark the given library function (*libfunc*) as unavailable.
        """
        ffi.lib.LLVMPY_SetUnavailableLibFunc(self, libfunc.identity)


LibFunc = collections.namedtuple("LibFunc", ["identity", "name"])

# ============================================================================
# FFI

ffi.lib.LLVMPY_GetDefaultTargetTriple.argtypes = [POINTER(c_char_p)]

ffi.lib.LLVMPY_GetHostCPUName.argtypes = [POINTER(c_char_p)]

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
ffi.lib.LLVMPY_ABISizeOfType.restype = c_longlong

ffi.lib.LLVMPY_ABISizeOfElementType.argtypes = [ffi.LLVMTargetDataRef,
                                                ffi.LLVMTypeRef]
ffi.lib.LLVMPY_ABISizeOfElementType.restype = c_longlong

ffi.lib.LLVMPY_ABIAlignmentOfElementType.argtypes = [ffi.LLVMTargetDataRef,
                                                     ffi.LLVMTypeRef]
ffi.lib.LLVMPY_ABIAlignmentOfElementType.restype = c_longlong

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

ffi.lib.LLVMPY_AddAnalysisPasses.argtypes = [
    ffi.LLVMTargetMachineRef,
    ffi.LLVMPassManagerRef,
]

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

ffi.lib.LLVMPY_CreateTargetLibraryInfo.argtypes = [c_char_p]
ffi.lib.LLVMPY_CreateTargetLibraryInfo.restype = ffi.LLVMTargetLibraryInfoRef

ffi.lib.LLVMPY_DisposeTargetLibraryInfo.argtypes = [
    ffi.LLVMTargetLibraryInfoRef,
]

ffi.lib.LLVMPY_AddTargetLibraryInfo.argtypes = [
    ffi.LLVMTargetLibraryInfoRef,
    ffi.LLVMPassManagerRef,
]

ffi.lib.LLVMPY_DisableAllBuiltins.argtypes = [
    ffi.LLVMTargetLibraryInfoRef,
]

ffi.lib.LLVMPY_GetLibFunc.argtypes = [
    ffi.LLVMTargetLibraryInfoRef,
    c_char_p,
    POINTER(c_int),
]
ffi.lib.LLVMPY_GetLibFunc.restype = c_int

ffi.lib.LLVMPY_SetUnavailableLibFunc.argtypes = [
    ffi.LLVMTargetLibraryInfoRef,
    c_int,
]

ffi.lib.LLVMPY_GetTargetMachineData.argtypes = [
    ffi.LLVMTargetMachineRef,
]
ffi.lib.LLVMPY_GetTargetMachineData.restype = ffi.LLVMTargetDataRef
