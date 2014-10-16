from __future__ import print_function, absolute_import
from ctypes import c_char_p, byref, POINTER, c_bool
from . import ffi
from .value import ValueRef


def parse_assembly(llvmir):
    """
    Create Module from a LLVM IR string
    """
    context = ffi.lib.LLVMPY_GetGlobalContext()
    strbuf = c_char_p(llvmir.encode('utf8'))
    with ffi.OutputString() as errmsg:
        module = ffi.lib.LLVMPY_ParseAssembly(context, strbuf, errmsg)
        if errmsg:
            ffi.lib.LLVMPY_DisposeModule(module)
            raise RuntimeError("LLVM IR parsing error\n{0}".format(errmsg))
    return ModuleRef(module)


class ModuleRef(ffi.ObjectRef):
    """A weak reference to a LLVM module.
    """

    def __str__(self):
        with ffi.OutputString() as outstr:
            ffi.lib.LLVMPY_PrintModuleToString(self, outstr)
            return str(outstr)

    def close(self):
        return ffi.lib.LLVMPY_DisposeModule(self)

    def get_function(self, name):
        p = ffi.lib.LLVMPY_GetNamedFunction(self, name.encode('utf8'))
        if not p:
            raise NameError(name)
        return ValueRef(p)

    def verify(self):
        with ffi.OutputString() as outmsg:
            if ffi.lib.LLVMPY_VerifyModule(self, outmsg):
                raise RuntimeError(outmsg)

    @property
    def data_layout(self):
        ffi.lib.LLVMPY_GetDataLayout(self)

    target_data = data_layout

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

ffi.lib.LLVMPY_GetDataLayout = [ffi.LLVMModuleRef,
                                POINTER(c_char_p)]
