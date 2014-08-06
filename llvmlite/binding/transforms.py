from __future__ import print_function, absolute_import
from ctypes import c_uint, c_bool
from . import ffi
from . import passmanagers


def create_pass_manager_builder():
    return PassManagerBuilder(ffi.lib.LLVMPY_PassManagerBuilderCreate())


class PassManagerBuilder(ffi.ObjectRef):
    def set_opt(self, level):
        ffi.lib.LLVMPY_PassManagerBuilderSetOptLevel(level)
        return self

    def set_size(self, level):
        ffi.lib.LLVMPY_PassManagerBuilderSetSizeLevel(level)
        return self

    def set_inline(self, threshold):
        ffi.lib.LLVMPY_PassManagerBuilderUseInlinerWithThreshold(threshold)
        return self

    def disable_unit_at_a_time(self, disable=True):
        ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnitAtATime(disable)

    def disable_unroll_loops(self, disable=True):
        ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnrollLoops(disable)

    def disable_simplify_lib_calls(self, disable=True):
        ffi.lib.LLVMPY_PassManagerBuilderSetDisableSimplifyLibCalls(disable)

    def _populate_module_pm(self, pm):
        ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManager(self, pm)

    def _populate_function_pm(self, pm):
        ffi.lib.LLVMPY_PassManagerBuilderPopulateFunctionPassManager(self, pm)

    def populate(self, pm):
        if isinstance(pm, passmanagers.ModulePassManager):
            self._populate_module_pm(pm)
        elif isinstance(pm, passmanagers.FunctionPassManager):
            self._populate_funciton_pm(pm)
        else:
            raise ValueError(pm)

    def close(self):
        ffi.lib.LLVMPY_PassManagerBuilderDispose(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# ============================================================================
# FFI

ffi.lib.LLVMPY_PassManagerBuilderCreate.restype = ffi.LLVMPassManagerBuilderRef

ffi.lib.LLVMPY_PassManagerBuilderDispose.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateModulePassManager.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    ffi.LLVMPassManagerRef,
]

ffi.lib.LLVMPY_PassManagerBuilderPopulateFunctionPassManager.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    ffi.LLVMPassManagerRef,
]

ffi.lib.LLVMPY_PassManagerBuilderSetOptLevel.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_uint,
]

ffi.lib.LLVMPY_PassManagerBuilderSetSizeLevel.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_uint,
]

ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnitAtATime.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_bool,
]

ffi.lib.LLVMPY_PassManagerBuilderSetDisableUnrollLoops.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_bool,
]

ffi.lib.LLVMPY_PassManagerBuilderSetDisableSimplifyLibCalls.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_bool,
]

ffi.lib.LLVMPY_PassManagerBuilderUseInlinerWithThreshold.argtypes = [
    ffi.LLVMPassManagerBuilderRef,
    c_uint,
]
