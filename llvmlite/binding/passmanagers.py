from ctypes import c_bool, c_int, c_size_t, c_uint, Structure, byref
from collections import namedtuple
from enum import IntFlag
from llvmlite.binding import ffi

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

    def add_aa_eval_pass(self):
        """See https://llvm.org/docs/Passes.html#aa-eval-exhaustive-alias-analysis-precision-evaluator."""  # noqa E501
        ffi.lib.LLVMPY_AddAAEvalPass(self)

    def add_basic_aa_pass(self):
        """See https://llvm.org/docs/Passes.html#basic-aa-basic-alias-analysis-stateless-aa-impl."""  # noqa E501
        ffi.lib.LLVMPY_AddBasicAAWrapperPass(self)

    def add_constant_merge_pass(self):
        """See http://llvm.org/docs/Passes.html#constmerge-merge-duplicate-global-constants."""  # noqa E501
        ffi.lib.LLVMPY_AddConstantMergePass(self)

    def add_dead_arg_elimination_pass(self):
        """See http://llvm.org/docs/Passes.html#deadargelim-dead-argument-elimination."""  # noqa E501
        ffi.lib.LLVMPY_AddDeadArgEliminationPass(self)

    def add_dependence_analysis_pass(self):
        """See https://llvm.org/docs/Passes.html#da-dependence-analysis"""  # noqa E501
        ffi.lib.LLVMPY_AddDependenceAnalysisPass(self)

    def add_dot_call_graph_pass(self):
        """See https://llvm.org/docs/Passes.html#dot-callgraph-print-call-graph-to-dot-file"""  # noqa E501
        ffi.lib.LLVMPY_AddCallGraphDOTPrinterPass(self)

    def add_dot_cfg_printer_pass(self):
        """See https://llvm.org/docs/Passes.html#dot-cfg-print-cfg-of-function-to-dot-file"""  # noqa E501
        ffi.lib.LLVMPY_AddCallGraphViewerPass(self)

    def add_dot_dom_printer_pass(self, show_body=False):
        """See https://llvm.org/docs/Passes.html#dot-dom-print-dominance-tree-of-function-to-dot-file"""  # noqa E501
        ffi.lib.LLVMPY_AddDotDomPrinterPass(self, show_body)

    def add_dot_postdom_printer_pass(self, show_body=False):
        """See https://llvm.org/docs/Passes.html#dot-postdom-print-postdominance-tree-of-function-to-dot-file"""  # noqa E501
        ffi.lib.LLVMPY_AddDotPostDomPrinterPass(self, show_body)

    def add_globals_mod_ref_aa_pass(self):
        """See https://llvm.org/docs/Passes.html#globalsmodref-aa-simple-mod-ref-analysis-for-globals"""  # noqa E501
        ffi.lib.LLVMPY_AddGlobalsModRefAAPass(self)

    def add_iv_users_pass(self):
        """See https://llvm.org/docs/Passes.html#iv-users-induction-variable-users"""  # noqa E501
        ffi.lib.LLVMPY_AddIVUsersPass(self)

    def add_lint_pass(self):
        """See https://llvm.org/docs/Passes.html#lint-statically-lint-checks-llvm-ir"""  # noqa E501
        ffi.lib.LLVMPY_AddLintPass(self)

    def add_lazy_value_info_pass(self):
        """See https://llvm.org/docs/Passes.html#lazy-value-info-lazy-value-information-analysis"""  # noqa E501
        ffi.lib.LLVMPY_AddLazyValueInfoPass(self)

    def add_intervals_pass(self):
        """See https://llvm.org/docs/Passes.html#intervals-interval-partition-construction"""  # noqa E501
        ffi.lib.LLVMPY_AddIntervalsPass(self)

    def add_module_debug_info_pass(self):
        """See https://llvm.org/docs/Passes.html#module-debuginfo-decodes-module-level-debug-info"""  # noqa E501
        ffi.lib.LLVMPY_AddModuleDebugInfoPrinterPass(self)

    def add_region_info_pass(self):
        """See https://llvm.org/docs/Passes.html#regions-detect-single-entry-single-exit-regions"""  # noqa E501
        ffi.lib.LLVMPY_AddRegionInfoPass(self)

    def add_scalar_evolution_aa_pass(self):
        """See https://llvm.org/docs/Passes.html#scev-aa-scalarevolution-based-alias-analysis"""  # noqa E501
        ffi.lib.LLVMPY_AddScalarEvolutionAAPass(self)

    def add_aggressive_dead_code_elimination_pass(self):
        """See https://llvm.org/docs/Passes.html#adce-aggressive-dead-code-elimination"""  # noqa E501
        ffi.lib.LLVMPY_AddAggressiveDCEPass(self)

    def add_always_inliner_pass(self, insert_lifetime=True):
        """See https://llvm.org/docs/Passes.html#always-inline-inliner-for-always-inline-functions"""  # noqa E501
        ffi.lib.LLVMPY_AddAlwaysInlinerPass(self, insert_lifetime)

    def add_arg_promotion_pass(self, max_elements=3):
        """See https://llvm.org/docs/Passes.html#argpromotion-promote-by-reference-arguments-to-scalars"""  # noqa E501
        ffi.lib.LLVMPY_AddArgPromotionPass(self, max_elements)

    def add_break_critical_edges_pass(self):
        """See https://llvm.org/docs/Passes.html#break-crit-edges-break-critical-edges-in-cfg"""  # noqa E501
        ffi.lib.LLVMPY_AddBreakCriticalEdgesPass(self)

    def add_dead_store_elimination_pass(self):
        """See https://llvm.org/docs/Passes.html#dse-dead-store-elimination"""  # noqa E501
        ffi.lib.LLVMPY_AddDeadStoreEliminationPass(self)

    def add_post_order_function_attrs_pass(self):
        """See https://llvm.org/docs/Passes.html#function-attrs-deduce-function-attributes"""  # noqa E501
        ffi.lib.LLVMPY_AddReversePostOrderFunctionAttrsPass(self)

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

    def add_aggressive_instruction_combining_pass(self):
        """See https://llvm.org/docs/Passes.html#aggressive-instcombine-combine-expression-patterns"""  # noqa E501
        ffi.lib.LLVMPY_AddAggressiveInstructionCombiningPass(self)

    def add_internalize_pass(self):
        """See https://llvm.org/docs/Passes.html#internalize-internalize-global-symbols"""  # noqa E501
        ffi.lib.LLVMPY_AddInternalizePass(self)

    def add_cfg_simplification_pass(self):
        """See http://llvm.org/docs/Passes.html#simplifycfg-simplify-the-cfg."""
        ffi.lib.LLVMPY_AddCFGSimplificationPass(self)

    def add_jump_threading_pass(self, threshold=-1):
        """See https://llvm.org/docs/Passes.html#jump-threading-jump-threading"""  # noqa E501
        ffi.lib.LLVMPY_AddJumpThreadingPass(self, threshold)

    def add_lcssa_pass(self):
        """See https://llvm.org/docs/Passes.html#lcssa-loop-closed-ssa-form-pass"""  # noqa E501
        ffi.lib.LLVMPY_AddLCSSAPass(self)

    def add_gvn_pass(self):
        """See http://llvm.org/docs/Passes.html#gvn-global-value-numbering."""
        ffi.lib.LLVMPY_AddGVNPass(self)

    def add_instruction_combining_pass(self):
        """See http://llvm.org/docs/Passes.html#passes-instcombine."""
        ffi.lib.LLVMPY_AddInstructionCombiningPass(self)

    def add_licm_pass(self):
        """See http://llvm.org/docs/Passes.html#licm-loop-invariant-code-motion."""  # noqa E501
        ffi.lib.LLVMPY_AddLICMPass(self)

    def add_loop_deletion_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-deletion-delete-dead-loops"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopDeletionPass(self)

    def add_loop_extractor_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-extract-extract-loops-into-new-functions"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopExtractorPass(self)

    def add_single_loop_extractor_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-extract-single-extract-at-most-one-loop-into-a-new-function"""  # noqa E501
        ffi.lib.LLVMPY_AddSingleLoopExtractorPass(self)

    def add_sccp_pass(self):
        """See http://llvm.org/docs/Passes.html#sccp-sparse-conditional-constant-propagation."""  # noqa E501
        ffi.lib.LLVMPY_AddSCCPPass(self)

    def add_loop_strength_reduce_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-reduce-loop-strength-reduction"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopStrengthReducePass(self)

    def add_loop_simplification_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-simplify-canonicalize-natural-loops"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopSimplificationPass(self)

    def add_loop_unroll_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-unroll-unroll-loops"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopUnrollPass(self)

    def add_loop_unroll_and_jam_pass(self):
        """See https://llvm.org/docs/Passes.html#loop-unroll-and-jam-unroll-and-jam-loops"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopUnrollAndJamPass(self)

    def add_loop_unswitch_pass(self,
                               optimize_for_size=False,
                               has_branch_divergence=False):
        """See https://llvm.org/docs/Passes.html#loop-unswitch-unswitch-loops"""  # noqa E501
        ffi.lib.LLVMPY_AddLoopUnswitchPass(self,
                                           optimize_for_size,
                                           has_branch_divergence)

    def add_lower_atomic_pass(self):
        """See https://llvm.org/docs/Passes.html#loweratomic-lower-atomic-intrinsics-to-non-atomic-form"""  # noqa E501
        ffi.lib.LLVMPY_AddLowerAtomicPass(self)

    def add_lower_invoke_pass(self):
        """See https://llvm.org/docs/Passes.html#lowerinvoke-lower-invokes-to-calls-for-unwindless-code-generators"""  # noqa E501
        ffi.lib.LLVMPY_AddLowerInvokePass(self)

    def add_lower_switch_pass(self):
        """See https://llvm.org/docs/Passes.html#lowerswitch-lower-switchinsts-to-branches"""  # noqa E501
        ffi.lib.LLVMPY_AddLowerSwitchPass(self)

    def add_memcpy_optimization_pass(self):
        """See https://llvm.org/docs/Passes.html#memcpyopt-memcpy-optimization"""  # noqa E501
        ffi.lib.LLVMPY_AddMemCpyOptimizationPass(self)

    def add_merge_functions_pass(self):
        """See https://llvm.org/docs/Passes.html#mergefunc-merge-functions"""  # noqa E501
        ffi.lib.LLVMPY_AddMergeFunctionsPass(self)

    def add_merge_returns_pass(self):
        """See https://llvm.org/docs/Passes.html#mergereturn-unify-function-exit-nodes"""  # noqa E501
        ffi.lib.LLVMPY_AddMergeReturnsPass(self)

    def add_partial_inlining_pass(self):
        """See https://llvm.org/docs/Passes.html#partial-inliner-partial-inliner"""  # noqa E501
        ffi.lib.LLVMPY_AddPartialInliningPass(self)

    def add_prune_exception_handling_pass(self):
        """See https://llvm.org/docs/Passes.html#prune-eh-remove-unused-exception-handling-info"""  # noqa E501
        ffi.lib.LLVMPY_AddPruneExceptionHandlingPass(self)

    def add_reassociate_expressions_pass(self):
        """See https://llvm.org/docs/Passes.html#reassociate-reassociate-expressions"""  # noqa E501
        ffi.lib.LLVMPY_AddReassociatePass(self)

    def add_demote_register_to_memory_pass(self):
        """See https://llvm.org/docs/Passes.html#rel-lookup-table-converter-relative-lookup-table-converter"""  # noqa E501
        ffi.lib.LLVMPY_AddDemoteRegisterToMemoryPass(self)

    def add_sroa_pass(self):
        """See http://llvm.org/docs/Passes.html#scalarrepl-scalar-replacement-of-aggregates-dt.
        Note that this pass corresponds to the ``opt -sroa`` command-line option,
        despite the link above."""  # noqa E501
        ffi.lib.LLVMPY_AddSROAPass(self)

    def add_sink_pass(self):
        """See https://llvm.org/docs/Passes.html#sink-code-sinking"""  # noqa E501
        ffi.lib.LLVMPY_AddSinkPass(self)

    def add_strip_symbols_pass(self, only_debug=False):
        """See https://llvm.org/docs/Passes.html#strip-strip-all-symbols-from-a-module"""  # noqa E501
        ffi.lib.LLVMPY_AddStripSymbolsPass(self, only_debug)

    def add_strip_dead_debug_info_pass(self):
        """See https://llvm.org/docs/Passes.html#strip-dead-debug-info-strip-debug-info-for-unused-symbols"""  # noqa E501
        ffi.lib.LLVMPY_AddStripDeadDebugInfoPass(self)

    def add_strip_dead_prototypes_pass(self):
        """See https://llvm.org/docs/Passes.html#strip-dead-prototypes-strip-unused-function-prototypes"""  # noqa E501
        ffi.lib.LLVMPY_AddStripDeadPrototypesPass(self)

    def add_strip_debug_declare_pass(self):
        """See https://llvm.org/docs/Passes.html#strip-debug-declare-strip-all-llvm-dbg-declare-intrinsics"""  # noqa E501
        ffi.lib.LLVMPY_AddStripDebugDeclarePrototypesPass(self)

    def add_strip_nondebug_symbols_pass(self):
        """See https://llvm.org/docs/Passes.html#strip-nondebug-strip-all-symbols-except-dbg-symbols-from-a-module"""  # noqa E501
        ffi.lib.LLVMPY_AddStripNondebugSymbolsPass(self)

    def add_tail_call_elimination_pass(self):
        """See https://llvm.org/docs/Passes.html#tailcallelim-tail-call-elimination"""  # noqa E501
        ffi.lib.LLVMPY_AddTailCallEliminationPass(self)

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

ffi.lib.LLVMPY_AddAAEvalPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddBasicAAWrapperPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddConstantMergePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDeadArgEliminationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDependenceAnalysisPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddCallGraphDOTPrinterPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddCallGraphViewerPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDotDomPrinterPass.argtypes = [ffi.LLVMPassManagerRef, c_bool]
ffi.lib.LLVMPY_AddDotPostDomPrinterPass.argtypes = [
    ffi.LLVMPassManagerRef,
    c_bool]
ffi.lib.LLVMPY_AddGlobalsModRefAAPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddInstructionCountPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddIVUsersPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLazyValueInfoPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLintPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddModuleDebugInfoPrinterPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddRegionInfoPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddScalarEvolutionAAPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddAggressiveDCEPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddAlwaysInlinerPass.argtypes = [ffi.LLVMPassManagerRef, c_bool]
ffi.lib.LLVMPY_AddArgPromotionPass.argtypes = [ffi.LLVMPassManagerRef, c_uint]
ffi.lib.LLVMPY_AddBreakCriticalEdgesPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDeadStoreEliminationPass.argtypes = [
    ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddReversePostOrderFunctionAttrsPass.argtypes = [
    ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddAggressiveInstructionCombiningPass.argtypes = [
    ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddInternalizePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLCSSAPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopDeletionPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopExtractorPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddSingleLoopExtractorPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopStrengthReducePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopStrengthReducePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopSimplificationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopUnrollPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopUnrollAndJamPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLoopUnswitchPass.argtypes = [
    ffi.LLVMPassManagerRef,
    c_bool,
    c_bool]
ffi.lib.LLVMPY_AddLoopUnrollPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLowerAtomicPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLowerInvokePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddLowerSwitchPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddMemCpyOptimizationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddMergeFunctionsPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddMergeReturnsPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddPartialInliningPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddPruneExceptionHandlingPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddReassociatePass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddDemoteRegisterToMemoryPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddSinkPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddStripSymbolsPass.argtypes = [ffi.LLVMPassManagerRef, c_bool]
ffi.lib.LLVMPY_AddStripDeadDebugInfoPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddStripDeadPrototypesPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddStripDebugDeclarePrototypesPass.argtypes = [
    ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddStripNondebugSymbolsPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddTailCallEliminationPass.argtypes = [ffi.LLVMPassManagerRef]
ffi.lib.LLVMPY_AddJumpThreadingPass.argtypes = [ffi.LLVMPassManagerRef, c_int]
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
