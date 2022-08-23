from ctypes import c_bool, c_char_p, c_int, c_size_t, Structure, byref
from collections import namedtuple
from enum import IntFlag
from llvmlite.binding import ffi
import os
from tempfile import mkstemp
from llvmlite.binding.common import _encode_string

_prunestats = namedtuple('PruneStats',
                         ('basicblock diamond fanout fanout_raise'))


class PruneStats(_prunestats):
    """ Holds statistics from reference count pruning.
    """

    def __add__(self, other):
        if not isinstance(other, PruneStats):
            msg = 'PruneStats can only be added to another PruneStats, got {}.'
            raise TypeError(msg.format(type(other)))
        return PruneStats(self.basicblock + other.basicblock,
                          self.diamond + other.diamond,
                          self.fanout + other.fanout,
                          self.fanout_raise + other.fanout_raise)

    def __sub__(self, other):
        if not isinstance(other, PruneStats):
            msg = ('PruneStats can only be subtracted from another PruneStats, '
                   'got {}.')
            raise TypeError(msg.format(type(other)))
        return PruneStats(self.basicblock - other.basicblock,
                          self.diamond - other.diamond,
                          self.fanout - other.fanout,
                          self.fanout_raise - other.fanout_raise)


class _c_PruneStats(Structure):
    _fields_ = [
        ('basicblock', c_size_t),
        ('diamond', c_size_t),
        ('fanout', c_size_t),
        ('fanout_raise', c_size_t)]


def dump_refprune_stats(printout=False):
    """ Returns a namedtuple containing the current values for the refop pruning
    statistics. If kwarg `printout` is True the stats are printed to stderr,
    default is False.
    """

    stats = _c_PruneStats(0, 0, 0, 0)
    do_print = c_bool(printout)

    ffi.lib.LLVMPY_DumpRefPruneStats(byref(stats), do_print)
    return PruneStats(stats.basicblock, stats.diamond, stats.fanout,
                      stats.fanout_raise)


def set_time_passes(enable):
    """Enable or disable the pass timers.

    Parameters
    ----------
    enable : bool
        Set to True to enable the pass timers.
        Set to False to disable the pass timers.
    """
    ffi.lib.LLVMPY_SetTimePasses(c_bool(enable))


def report_and_reset_timings():
    """Returns the pass timings report and resets the LLVM internal timers.

    Pass timers are enabled by ``set_time_passes()``. If the timers are not
    enabled, this function will return an empty string.

    Returns
    -------
    res : str
        LLVM generated timing report.
    """
    with ffi.OutputString() as buf:
        ffi.lib.LLVMPY_ReportAndResetTimings(buf)
        return str(buf)


def create_module_pass_manager():
    return ModulePassManager()


def create_function_pass_manager(module):
    return FunctionPassManager(module)


class RefPruneSubpasses(IntFlag):
    PER_BB       = 0b0001    # noqa: E221
    DIAMOND      = 0b0010    # noqa: E221
    FANOUT       = 0b0100    # noqa: E221
    FANOUT_RAISE = 0b1000
    ALL = PER_BB | DIAMOND | FANOUT | FANOUT_RAISE


class PassManager(ffi.ObjectRef):
    """PassManager
    """

    def _dispose(self):
        self._capi.LLVMPY_DisposePassManager(self)

    def add_constant_merge_pass(self):
        """See http://llvm.org/docs/Passes.html#constmerge-merge-duplicate-global-constants."""  # noqa E501
        ffi.lib.LLVMPY_AddConstantMergePass(self)

    def add_dead_arg_elimination_pass(self):
        """See http://llvm.org/docs/Passes.html#deadargelim-dead-argument-elimination."""  # noqa E501
        ffi.lib.LLVMPY_AddDeadArgEliminationPass(self)

    def add_function_attrs_pass(self):
        """See http://llvm.org/docs/Passes.html#functionattrs-deduce-function-attributes."""  # noqa E501
        ffi.lib.LLVMPY_AddFunctionAttrsPass(self)

    def add_function_inlining_pass(self, threshold):
        """See http://llvm.org/docs/Passes.html#inline-function-integration-inlining."""  # noqa E501
        ffi.lib.LLVMPY_AddFunctionInliningPass(self, threshold)

    def add_global_dce_pass(self):
        """See http://llvm.org/docs/Passes.html#globaldce-dead-global-elimination."""  # noqa E501
        ffi.lib.LLVMPY_AddGlobalDCEPass(self)

    def add_global_optimizer_pass(self):
        """See http://llvm.org/docs/Passes.html#globalopt-global-variable-optimizer."""  # noqa E501
        ffi.lib.LLVMPY_AddGlobalOptimizerPass(self)

    def add_ipsccp_pass(self):
        """See http://llvm.org/docs/Passes.html#ipsccp-interprocedural-sparse-conditional-constant-propagation."""  # noqa E501
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
        """See http://llvm.org/docs/Passes.html#licm-loop-invariant-code-motion."""  # noqa E501
        ffi.lib.LLVMPY_AddLICMPass(self)

    def add_sccp_pass(self):
        """See http://llvm.org/docs/Passes.html#sccp-sparse-conditional-constant-propagation."""  # noqa E501
        ffi.lib.LLVMPY_AddSCCPPass(self)

    def add_sroa_pass(self):
        """See http://llvm.org/docs/Passes.html#scalarrepl-scalar-replacement-of-aggregates-dt.
        Note that this pass corresponds to the ``opt -sroa`` command-line option,
        despite the link above."""  # noqa E501
        ffi.lib.LLVMPY_AddSROAPass(self)

    def add_type_based_alias_analysis_pass(self):
        ffi.lib.LLVMPY_AddTypeBasedAliasAnalysisPass(self)

    def add_basic_alias_analysis_pass(self):
        """See http://llvm.org/docs/AliasAnalysis.html#the-basicaa-pass."""
        ffi.lib.LLVMPY_AddBasicAliasAnalysisPass(self)

    def add_loop_rotate_pass(self):
        """http://llvm.org/docs/Passes.html#loop-rotate-rotate-loops."""
        ffi.lib.LLVMPY_LLVMAddLoopRotatePass(self)

    # Non-standard LLVM passes

    def add_refprune_pass(self, subpasses_flags=RefPruneSubpasses.ALL,
                          subgraph_limit=1000):
        """Add Numba specific Reference count pruning pass.

        Parameters
        ----------
        subpasses_flags : RefPruneSubpasses
            A bitmask to control the subpasses to be enabled.
        subgraph_limit : int
            Limit the fanout pruners to working on a subgraph no bigger than
            this number of basic-blocks to avoid spending too much time in very
            large graphs. Default is 1000. Subject to change in future
            versions.
        """
        iflags = RefPruneSubpasses(subpasses_flags)
        ffi.lib.LLVMPY_AddRefPrunePass(self, iflags, subgraph_limit)


class ModulePassManager(PassManager):

    def __init__(self, ptr=None):
        if ptr is None:
            ptr = ffi.lib.LLVMPY_CreatePassManager()
        PassManager.__init__(self, ptr)

    def run(self, module, remarks_file=None, remarks_format='yaml',
            remarks_filter=''):
        """
        Run optimization passes on the given module.

        Parameters
        ----------
        module : llvmlite.binding.ModuleRef
            The module to be optimized inplace
        remarks_file : str; optional
            If not `None`, it is the file to store the optimization remarks.
        remarks_format : str; optional
            The format to write; YAML is default
        remarks_filter : str; optional
            The filter that should be applied to the remarks output.
        """
        if remarks_file is None:
            return ffi.lib.LLVMPY_RunPassManager(self, module)
        else:
            r = ffi.lib.LLVMPY_RunPassManagerWithRemarks(
                self, module, _encode_string(remarks_format),
                _encode_string(remarks_filter),
                _encode_string(remarks_file))
            if r == -1:
                raise IOError("Failed to initialize remarks file.")
            return r > 0

    def run_with_remarks(self, module, remarks_format='yaml',
                         remarks_filter=''):
        """
        Run optimization passes on the given module and returns the result and
        the remarks data.

        Parameters
        ----------
        module : llvmlite.binding.ModuleRef
            The module to be optimized
        remarks_format : str
            The remarks output; YAML is the default
        remarks_filter : str; optional
            The filter that should be applied to the remarks output.
        """
        remarkdesc, remarkfile = mkstemp()
        try:
            with os.fdopen(remarkdesc, 'r'):
                pass
            r = self.run(module, remarkfile, remarks_format, remarks_filter)
            if r == -1:
                raise IOError("Failed to initialize remarks file.")
            with open(remarkfile) as f:
                return bool(r), f.read()
        finally:
            os.unlink(remarkfile)


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

    def run(self, function, remarks_file=None, remarks_format='yaml',
            remarks_filter=''):
        """
        Run optimization passes on the given function.

        Parameters
        ----------
        function : llvmlite.binding.FunctionRef
            The function to be optimized inplace
        remarks_file : str; optional
            If not `None`, it is the file to store the optimization remarks.
        remarks_format : str; optional
            The format of the remarks file; the default is YAML
        remarks_filter : str; optional
            The filter that should be applied to the remarks output.
        """
        if remarks_file is None:
            return ffi.lib.LLVMPY_RunFunctionPassManager(self, function)
        else:
            r = ffi.lib.LLVMPY_RunFunctionPassManagerWithRemarks(
                self, function, _encode_string(remarks_format),
                _encode_string(remarks_filter),
                _encode_string(remarks_file))
            if r == -1:
                raise IOError("Failed to initialize remarks file.")
            return bool(r)

    def run_with_remarks(self, function, remarks_format='yaml',
                         remarks_filter=''):
        """
        Run optimization passes on the given function and returns the result
        and the remarks data.

        Parameters
        ----------
        function : llvmlite.binding.FunctionRef
            The function to be optimized inplace
        remarks_format : str; optional
            The format of the remarks file; the default is YAML
        remarks_filter : str; optional
            The filter that should be applied to the remarks output.
        """
        # LLVM is going to need to close this file and then reopen it, so we
        # can't use an unlinked temporary file.
        remarkdesc, remarkfile = mkstemp()
        try:
            # We get an open handle, but we need LLVM to write first, so close
            # it.
            with os.fdopen(remarkdesc, 'r'):
                pass
            r = self.run(function, remarkfile, remarks_format, remarks_filter)
            if r == -1:
                raise IOError("Failed to initialize remarks file.")
            with open(remarkfile) as f:
                return bool(r), f.read()
        finally:
            os.unlink(remarkfile)


# ============================================================================
# FFI

ffi.lib.LLVMPY_CreatePassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_CreateFunctionPassManager.argtypes = [ffi.LLVMModuleRef]
ffi.lib.LLVMPY_CreateFunctionPassManager.restype = ffi.LLVMPassManagerRef

ffi.lib.LLVMPY_DisposePassManager.argtypes = [ffi.LLVMPassManagerRef]

ffi.lib.LLVMPY_RunPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                          ffi.LLVMModuleRef]
ffi.lib.LLVMPY_RunPassManager.restype = c_bool

ffi.lib.LLVMPY_RunPassManagerWithRemarks.argtypes = [ffi.LLVMPassManagerRef,
                                                     ffi.LLVMModuleRef,
                                                     c_char_p,
                                                     c_char_p,
                                                     c_char_p]
ffi.lib.LLVMPY_RunPassManagerWithRemarks.restype = c_int

ffi.lib.LLVMPY_InitializeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_InitializeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_FinalizeFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_FinalizeFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_RunFunctionPassManager.argtypes = [ffi.LLVMPassManagerRef,
                                                  ffi.LLVMValueRef]
ffi.lib.LLVMPY_RunFunctionPassManager.restype = c_bool

ffi.lib.LLVMPY_RunFunctionPassManagerWithRemarks.argtypes = [
    ffi.LLVMPassManagerRef, ffi.LLVMValueRef, c_char_p, c_char_p, c_char_p
]
ffi.lib.LLVMPY_RunFunctionPassManagerWithRemarks.restype = c_int

ffi.lib.LLVMPY_AddConstantMergePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDeadArgEliminationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddFunctionAttrsPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddFunctionInliningPass.argtypes = [
    ffi.LLVMPassManagerRef, c_int]
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

ffi.lib.LLVMPY_AddRefPrunePass.argtypes = [ffi.LLVMPassManagerRef, c_int,
                                           c_size_t]
