from __future__ import print_function, absolute_import
import os
import sys
from ctypes import c_bool, c_int, c_char_p, cdll, CDLL, POINTER, RTLD_LOCAL
from collections import namedtuple
from . import ffi

def create_module_pass_manager():
    return ModulePassManager()


def create_function_pass_manager(module):
    return FunctionPassManager(module)


# we maintain a global list of loaded libraries. On pypy,
# garbage collection dlcloses loaded libraries which makes it
# virtually impossible to handle pass registration properly
# setdlopenflags also doesn't work properly on pypy
_loaded_libraries = []


def load_pass_plugin(path):
    """Load shared library containing a pass"""
    pass_lib = CDLL(path, RTLD_LOCAL)
    pass_lib.LLVMPY_RegisterPass(get_pass_registry())
    _loaded_libraries.append(pass_lib)

class PassRegistry(ffi.ObjectRef):
    """
        Return the names of the registered passes as a list
        of tuples (<pass arg>, <pass name>)
    """
    def list_registered_passes(self):
        PassInfo = namedtuple("PassInfo", ["arg", "name"])
        with ffi.OutputString() as out:
            ffi.lib.LLVMPY_ListRegisteredPasses(self, out)
            passes = [PassInfo(*pass_info.split(":", 1))\
                             for pass_info in str(out).split(',')]
            return passes

def get_pass_registry():
    return PassRegistry(ffi.lib.LLVMPY_GetPassRegistry())

class PassManager(ffi.ObjectRef):
    """PassManager
    """

    def __init__(self, ptr):
        super(PassManager, self).__init__(ptr)

    def _dispose(self):
        # unload shared libraries
        self._capi.LLVMPY_DisposePassManager(self)

    def add_constant_merge_pass(self):
        """See http://llvm.org/docs/Passes.html#constmerge-merge-duplicate-global-constants."""
        ffi.lib.LLVMPY_AddConstantMergePass(self)

    def add_dead_arg_elimination_pass(self):
        """See http://llvm.org/docs/Passes.html#deadargelim-dead-argument-elimination."""
        ffi.lib.LLVMPY_AddDeadArgEliminationPass(self)

    def add_function_attrs_pass(self):
        """See http://llvm.org/docs/Passes.html#functionattrs-deduce-function-attributes."""
        ffi.lib.LLVMPY_AddFunctionAttrsPass(self)

    def add_function_inlining_pass(self, threshold):
        """See http://llvm.org/docs/Passes.html#inline-function-integration-inlining."""
        ffi.lib.LLVMPY_AddFunctionInliningPass(self, threshold)

    def add_global_dce_pass(self):
        """See http://llvm.org/docs/Passes.html#globaldce-dead-global-elimination."""
        ffi.lib.LLVMPY_AddGlobalDCEPass(self)

    def add_global_optimizer_pass(self):
        """See http://llvm.org/docs/Passes.html#globalopt-global-variable-optimizer."""
        ffi.lib.LLVMPY_AddGlobalOptimizerPass(self)

    def add_ipsccp_pass(self):
        """See http://llvm.org/docs/Passes.html#ipsccp-interprocedural-sparse-conditional-constant-propagation."""
        ffi.lib.LLVMPY_AddIPSCCPPass(self)

    def add_dead_code_elimination_pass(self):
        """See http://llvm.org/docs/Passes.html#dce-dead-code-elimination."""
        ffi.lib.LLVMPY_AddDeadCodeEliminationPass(self)

    def add_cfg_simplification_pass(self):
        """See http://llvm.org/docs/Passes.html#simplifycfg-simplify-the-cfg."""
        ffi.lib.LLVMPY_AddCFGSimplificationPass(self)

    def add_gvn_pass(self):
        """See http://llvm.org/docs/Passes.html#gvn-global-value-numbering."""
        ffi.lib.LLVMPY_AddGVNPass(self)

    def add_instruction_combining_pass(self):
        """See http://llvm.org/docs/Passes.html#passes-instcombine."""
        ffi.lib.LLVMPY_AddInstructionCombiningPass(self)

    def add_licm_pass(self):
        """See http://llvm.org/docs/Passes.html#licm-loop-invariant-code-motion."""
        ffi.lib.LLVMPY_AddLICMPass(self)

    def add_sccp_pass(self):
        """See http://llvm.org/docs/Passes.html#sccp-sparse-conditional-constant-propagation."""
        ffi.lib.LLVMPY_AddSCCPPass(self)

    def add_sroa_pass(self):
        """See http://llvm.org/docs/Passes.html#scalarrepl-scalar-replacement-of-aggregates-dt.
        Note that this pass corresponds to the ``opt -sroa`` command-line option,
        despite the link above."""
        ffi.lib.LLVMPY_AddSROAPass(self)

    def add_type_based_alias_analysis_pass(self):
        ffi.lib.LLVMPY_AddTypeBasedAliasAnalysisPass(self)

    def add_basic_alias_analysis_pass(self):
        """See http://llvm.org/docs/AliasAnalysis.html#the-basicaa-pass."""
        ffi.lib.LLVMPY_AddBasicAliasAnalysisPass(self)

    def add_pass_by_arg(self, pass_arg):
        """Add a pass using its registered name"""
        if not ffi.lib.LLVMPY_AddPassByArg(self, pass_arg.encode("utf8")):
            raise ValueError("Could not add pass '{}'".format(pass_arg))


class ModulePassManager(PassManager):

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_CreatePassManager()
        PassManager.__init__(self, ptr)

    def run(self, module):
        """
        Run optimization passes on the given module.
        """
        return ffi.lib.LLVMPY_RunPassManager(self, module)


class FunctionPassManager(PassManager):

    def __init__(self, module):
        ptr = ffi.lib.LLVMPY_CreateFunctionPassManager(module)
        self._module = module
        module._owned = True
        PassManager.__init__(self, ptr)

    def initialize(self):
        """
        Initialize the FunctionPassManager.  Returns True if it produced
        any changes (?).
        """
        return ffi.lib.LLVMPY_InitializeFunctionPassManager(self)

    def finalize(self):
        """
        Finalize the FunctionPassManager.  Returns True if it produced
        any changes (?).
        """
        return ffi.lib.LLVMPY_FinalizeFunctionPassManager(self)

    def run(self, function):
        """
        Run optimization passes on the given function.
        """
        return ffi.lib.LLVMPY_RunFunctionPassManager(self, function)


# ============================================================================
# FFI

ffi.lib.LLVMPY_CreatePassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_CreateFunctionPassManager.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_CreateFunctionPassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_DisposePassManager.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_RunPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                          ffi.LLVMModuleRef]
ffi.lib.LLVMPY_RunPassManager.restype = c_bool

ffi.lib.LLVMPY_InitializeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_InitializeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_FinalizeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_FinalizeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_RunFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                                  ffi.LLVMValueRef]
ffi.lib.LLVMPY_RunFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_AddConstantMergePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDeadArgEliminationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddFunctionAttrsPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddFunctionInliningPass.argtypes = [ffi.LLVMPassManagerRef, c_int]
ffi.lib.LLVMPY_AddGlobalDCEPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddGlobalOptimizerPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddIPSCCPPass.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_AddDeadCodeEliminationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddCFGSimplificationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddGVNPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddInstructionCombiningPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLICMPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddSCCPPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddSROAPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddTypeBasedAliasAnalysisPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddBasicAliasAnalysisPass.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_GetPassRegistry.argtypes = []
ffi.lib.LLVMPY_GetPassRegistry.restype = ffi.LLVMPassRegistryRef
ffi.lib.LLVMPY_ListRegisteredPasses.argtypes = [ffi.LLVMPassRegistryRef, POINTER(c_char_p)]
ffi.lib.LLVMPY_AddPassByArg.argtypes = [ffi.LLVMPassManagerRef, c_char_p]
ffi.lib.LLVMPY_AddPassByArg.restype = c_bool
