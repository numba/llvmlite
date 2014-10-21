from __future__ import print_function, absolute_import
from ctypes import c_char_p, byref, POINTER, c_bool
from . import ffi, link_modules
from .value import ValueRef


def parse_assembly(llvmir):
    """
    Create Module from a LLVM IR string
    """
    context = ffi.lib.LLVMPY_GetGlobalContext()
    strbuf = c_char_p(llvmir.encode('utf8'))
    with ffi.OutputString() as errmsg:
        mod = ModuleRef(ffi.lib.LLVMPY_ParseAssembly(context, strbuf, errmsg))
        if errmsg:
            mod.close()
            raise RuntimeError("LLVM IR parsing error\n{0}".format(errmsg))
    return mod


class ModuleRef(ffi.ObjectRef):
    """A weak reference to a LLVM module.
    """

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintModuleToString(self, outstr)
            return str(outstr)

    def close(self):
        if not self._closed:
            ffi.lib.LLVMPY_DisposeModule(self)
            ffi.ObjectRef.close(self)

    def get_function(self, name):
        p = ffi.lib.LLVMPY_GetNamedFunction(self, name.encode('utf8'))
        if not p:
            raise NameError(name)
        return ValueRef(p, module=self)

    def get_global_variable(self, name):
        p = ffi.lib.LLVMPY_GetNamedGlobalVariable(self, name.encode('utf8'))
        if not p:
            raise NameError(name)
        return ValueRef(p, module=self)

    def verify(self):
        with ffi.OutputString() as outmsg:
            if ffi.lib.LLVMPY_VerifyModule(self, outmsg):
                raise RuntimeError(str(outmsg))

    @property
    def data_layout(self):
        # LLVMGetDataLayout() points inside a std::string managed by LLVM.
        with ffi.OutputString(owned=False) as outmsg:
            ffi.lib.LLVMPY_GetDataLayout(self, outmsg)
            return str(outmsg)

    def link_in(self, other, preserve=False):
        link_modules(self, other, preserve)
        if not preserve:
            other.detach()


# =============================================================================
# Set function FFI

ffi.lib.LLVMPY_ParseAssembly.argtypes = [ffi.LLVMContextRef,
                                         c_char_p,
                                         POINTER(c_char_p)]
ffi.lib.LLVMPY_ParseAssembly.restype = ffi.LLVMModuleRef

ffi.lib.LLVMPY_GetGlobalContext.restype = ffi.LLVMContextRef

ffi.lib.LLVMPY_DisposeModule.argtypes = [ffi.LLVMModuleRef]

ffi.lib.LLVMPY_PrintModuleToString.argtypes = [ffi.LLVMModuleRef,
                                               POINTER(c_char_p)]

ffi.lib.LLVMPY_GetNamedFunction.argtypes = [ffi.LLVMModuleRef,
                                            c_char_p]
ffi.lib.LLVMPY_GetNamedFunction.restype = ffi.LLVMValueRef

ffi.lib.LLVMPY_VerifyModule.argtypes = [ffi.LLVMModuleRef,
                                        POINTER(c_char_p)]
ffi.lib.LLVMPY_VerifyModule.restype = c_bool

ffi.lib.LLVMPY_GetDataLayout.argtypes = [ffi.LLVMModuleRef, POINTER(c_char_p)]

ffi.lib.LLVMPY_GetNamedGlobalVariable.argtypes = [ffi.LLVMModuleRef, c_char_p]
ffi.lib.LLVMPY_GetNamedGlobalVariable.restype = ffi.LLVMValueRef
