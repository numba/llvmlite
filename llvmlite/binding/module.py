from __future__ import print_function, absolute_import
from ctypes import (c_char_p, byref, POINTER, c_bool, create_string_buffer,
                    c_void_p, c_size_t, cast, string_at)

from . import ffi
from .linker import link_modules
from .common import _decode_string, _encode_string
from .value import ValueRef


def parse_assembly(llvmir):
    """
    Create Module from a LLVM IR string
    """
    context = ffi.lib.LLVMPY_GetGlobalContext()
    llvmir = _encode_string(llvmir)
    strbuf = c_char_p(llvmir)
    with ffi.OutputString() as errmsg:
        mod = ModuleRef(ffi.lib.LLVMPY_ParseAssembly(context, strbuf, errmsg))
        if errmsg:
            mod.close()
            raise RuntimeError("LLVM IR parsing error\n{0}".format(errmsg))
    return mod


def parse_bitcode(bitcode):
    """
    Create Module from a LLVM *bitcode* (a bytes object).
    """
    context = ffi.lib.LLVMPY_GetGlobalContext()
    buf = c_char_p(bitcode)
    bufsize = len(bitcode)
    with ffi.OutputString() as errmsg:
        mod = ModuleRef(ffi.lib.LLVMPY_ParseBitcode(context, buf, bufsize, errmsg))
        if errmsg:
            mod.close()
            raise RuntimeError("LLVM bitcode parsing error\n{0}".format(errmsg))
    return mod


class ModuleRef(ffi.ObjectRef):
    """
    A reference to a LLVM module.
    """

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintModuleToString(self, outstr)
            return str(outstr)

    def as_bitcode(self):
        """
        Return the module's LLVM bitcode, as a bytes object.
        """
        ptr = c_char_p(None)
        size = c_size_t(-1)
        ffi.lib.LLVMPY_WriteBitcodeToString(self, byref(ptr), byref(size))
        if not ptr:
            raise MemoryError
        try:
            assert size.value >= 0
            return string_at(ptr, size.value)
        finally:
            ffi.lib.LLVMPY_DisposeString(ptr)

    def _dispose(self):
        self._capi.LLVMPY_DisposeModule(self)

    def get_function(self, name):
        """
        Get a ValueRef pointing to the function named *name*.
        NameError is raised if the symbol isn't found.
        """
        p = ffi.lib.LLVMPY_GetNamedFunction(self, _encode_string(name))
        if not p:
            raise NameError(name)
        return ValueRef(p, module=self)

    def get_global_variable(self, name):
        """
        Get a ValueRef pointing to the global variable named *name*.
        NameError is raised if the symbol isn't found.
        """
        p = ffi.lib.LLVMPY_GetNamedGlobalVariable(self, _encode_string(name))
        if not p:
            raise NameError(name)
        return ValueRef(p, module=self)

    def verify(self):
        """
        Verify the module IR's correctness.  RuntimeError is raised on error.
        """
        with ffi.OutputString() as outmsg:
            if ffi.lib.LLVMPY_VerifyModule(self, outmsg):
                raise RuntimeError(str(outmsg))

    @property
    def name(self):
        """
        The module's identifier.
        """
        return _decode_string(ffi.lib.LLVMPY_GetModuleName(self))

    @name.setter
    def name(self, value):
        ffi.lib.LLVMPY_SetModuleName(self, _encode_string(value))

    @property
    def data_layout(self):
        """
        This module's data layout specification, as a string.
        """
        # LLVMGetDataLayout() points inside a std::string managed by LLVM.
        with ffi.OutputString(owned=False) as outmsg:
            ffi.lib.LLVMPY_GetDataLayout(self, outmsg)
            return str(outmsg)

    @data_layout.setter
    def data_layout(self, strrep):
        ffi.lib.LLVMPY_SetDataLayout(self,
                                     create_string_buffer(
                                         strrep.encode('utf8')))

    @property
    def triple(self):
        """
        This module's target "triple" specification, as a string.
        """
        # LLVMGetTarget() points inside a std::string managed by LLVM.
        with ffi.OutputString(owned=False) as outmsg:
            ffi.lib.LLVMPY_GetTarget(self, outmsg)
            return str(outmsg)

    @triple.setter
    def triple(self, strrep):
        ffi.lib.LLVMPY_SetTarget(self,
                                 create_string_buffer(
                                     strrep.encode('utf8')))

    def link_in(self, other, preserve=False):
        link_modules(self, other, preserve)
        if not preserve:
            other.close()

    @property
    def global_variables(self):
        """
        Return an iterator over this module's global variables.
        The iterator will yield a ValueRef for each global variable.

        Note that global variables don't include functions
        (a function is a "global value" but not a "global variable" in
         LLVM parlance)
        """
        it = ffi.lib.LLVMPY_ModuleGlobalsIter(self)
        return _GlobalsIterator(it, module=self)

    @property
    def functions(self):
        """
        Return an iterator over this module's functions.
        The iterator will yield a ValueRef for each function.
        """
        it = ffi.lib.LLVMPY_ModuleFunctionsIter(self)
        return _FunctionsIterator(it, module=self)

    def clone(self):
        return ModuleRef(ffi.lib.LLVMPY_CloneModule(self))


class _Iterator(ffi.ObjectRef):

    def __init__(self, ptr, module):
        ffi.ObjectRef.__init__(self, ptr)
        # Keep Module alive
        self._module = module

    def __next__(self):
        vp = self._next()
        if vp:
            return ValueRef(vp, self._module)
        else:
            raise StopIteration

    next = __next__

    def __iter__(self):
        return self


class _GlobalsIterator(_Iterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeGlobalsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_GlobalsIterNext(self)


class _FunctionsIterator(_Iterator):

    def _dispose(self):
        self._capi.LLVMPY_DisposeFunctionsIter(self)

    def _next(self):
        return ffi.lib.LLVMPY_FunctionsIterNext(self)


# =============================================================================
# Set function FFI

ffi.lib.LLVMPY_ParseAssembly.argtypes = [ffi.LLVMContextRef,
                                         c_char_p,
                                         POINTER(c_char_p)]
ffi.lib.LLVMPY_ParseAssembly.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_ParseBitcode.argtypes = [ffi.LLVMContextRef,
                                        c_char_p, c_size_t,
                                        POINTER(c_char_p)]
ffi.lib.LLVMPY_ParseBitcode.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetGlobalContext.restype = ffi.LLVMContextRef

ffi.lib.LLVMPY_DisposeModule.argtypes = [ffi.LLVMModuleRef]

ffi.lib.LLVMPY_PrintModuleToString.argtypes = [ffi.LLVMModuleRef,
                                               POINTER(c_char_p)]
ffi.lib.LLVMPY_WriteBitcodeToString.argtypes = [ffi.LLVMModuleRef,
                                                POINTER(c_char_p),
                                                POINTER(c_size_t)]

ffi.lib.LLVMPY_GetNamedFunction.argtypes = [ffi.LLVMModuleRef,
                                            c_char_p]
ffi.lib.LLVMPY_GetNamedFunction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_VerifyModule.argtypes = [ffi.LLVMModuleRef,
                                        POINTER(c_char_p)]
ffi.lib.LLVMPY_VerifyModule.restype = c_bool

ffi.lib.LLVMPY_GetDataLayout.argtypes = [ffi.LLVMModuleRef, POINTER(c_char_p)]
ffi.lib.LLVMPY_SetDataLayout.argtypes = [ffi.LLVMModuleRef, c_char_p]

ffi.lib.LLVMPY_GetTarget.argtypes = [ffi.LLVMModuleRef, POINTER(c_char_p)]
ffi.lib.LLVMPY_SetTarget.argtypes = [ffi.LLVMModuleRef, c_char_p]

ffi.lib.LLVMPY_GetNamedGlobalVariable.argtypes = [ffi.LLVMModuleRef, c_char_p]
ffi.lib.LLVMPY_GetNamedGlobalVariable.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_ModuleGlobalsIter.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_ModuleGlobalsIter.restype = ffi.LLVMGlobalsIterator

ffi.lib.LLVMPY_DisposeGlobalsIter.argtypes = [ffi.LLVMGlobalsIterator]

ffi.lib.LLVMPY_GlobalsIterNext.argtypes = [ffi.LLVMGlobalsIterator]
ffi.lib.LLVMPY_GlobalsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_ModuleFunctionsIter.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_ModuleFunctionsIter.restype = ffi.LLVMFunctionsIterator

ffi.lib.LLVMPY_DisposeFunctionsIter.argtypes = [ffi.LLVMFunctionsIterator]

ffi.lib.LLVMPY_FunctionsIterNext.argtypes = [ffi.LLVMFunctionsIterator]
ffi.lib.LLVMPY_FunctionsIterNext.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_CloneModule.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_CloneModule.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetModuleName.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_GetModuleName.restype = c_char_p

ffi.lib.LLVMPY_SetModuleName.argtypes = [ffi.LLVMModuleRef, c_char_p]
