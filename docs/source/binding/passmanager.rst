
Optimization passes
===================

.. currentmodule:: llvmlite.binding


LLVM gives you the possibility to fine-tune optimization passes.  llvmlite
exposes several of these parameters.  Optimization passes are managed by
a pass manager; there are two kinds thereof: :class:`FunctionPassManager`,
for optimizations which work on single functions, and
:class:`ModulePassManager`, for optimizations which work on whole modules.

To instantiate any of those pass managers, you first have to create and
configure a :class:`PassManagerBuilder`.


.. class:: PassManagerBuilder()

   Create a new pass manager builder.  This object centralizes optimization
   settings.  The following method is available:

   .. method:: populate(pm)

      Populate the pass manager *pm* with the optimization passes configured
      in this pass manager builder.

   The following writable properties are also available:

   .. attribute:: disable_unroll_loops

      If true, disable loop unrolling.

   .. attribute:: inlining_threshold

      The integer threshold for inlining a function into another.  The higher,
      the more likely inlining a function is.  This attribute is write-only.

   .. attribute:: loop_vectorize

      If true, allow vectorizing loops.

   .. attribute:: opt_level

      The general optimization level as an integer between 0 and 3.

   .. attribute:: size_level

      Whether and how much to optimize for size.  An integer between 0 and 2.

   .. attribute:: slp_vectorize

      If true, enable the "SLP vectorizer", which uses a different algorithm
      from the loop vectorizer.  Both may be enabled at the same time.


.. class:: PassManager

   The base class for pass managers. Use individual ``add_*`` methods
   or :meth:`PassManagerBuilder.populate` to add optimization passes.


   .. function:: add_constant_merge_pass()

      See `constmerge pass documentation <http://llvm.org/docs/Passes.html#constmerge-merge-duplicate-global-constants>`_.

   .. function:: add_dead_arg_elimination_pass()

      See `deadargelim pass documentation <http://llvm.org/docs/Passes.html#deadargelim-dead-argument-elimination>`_.

   .. function:: add_function_attrs_pass()

      See `functionattrs pass documentation <http://llvm.org/docs/Passes.html#functionattrs-deduce-function-attributes>`_.

   .. function:: add_function_inlining_pass(self, )

      See `inline pass documentation <http://llvm.org/docs/Passes.html#inline-function-integration-inlining>`_.

   .. function:: add_global_dce_pass()

      See `globaldce pass documentation <http://llvm.org/docs/Passes.html#globaldce-dead-global-elimination>`_.

   .. function:: add_global_optimizer_pass()

      See `globalopt pass documentation <http://llvm.org/docs/Passes.html#globalopt-global-variable-optimizer>`_.

   .. function:: add_ipsccp_pass()

      See `ipsccp pass documentation <http://llvm.org/docs/Passes.html#ipsccp-interprocedural-sparse-conditional-constant-propagation>`_.

   .. function:: add_dead_code_elimination_pass()

      See `dce pass documentation <http://llvm.org/docs/Passes.html#dce-dead-code-elimination>`_.

   .. function:: add_cfg_simplification_pass()

      See `simplifycfg pass documentation <http://llvm.org/docs/Passes.html#simplifycfg-simplify-the-cfg>`_.

   .. function:: add_gvn_pass()

      See `gvn pass documentation <http://llvm.org/docs/Passes.html#gvn-global-value-numbering>`_.

   .. function:: add_instruction_combining_pass()

      See `instcombine pass documentation <http://llvm.org/docs/Passes.html#passes-instcombine>`_.

   .. function:: add_licm_pass()

      See `licm pass documentation <http://llvm.org/docs/Passes.html#licm-loop-invariant-code-motion>`_.

   .. function:: add_sccp_pass()

      See `sccp pass documentation <http://llvm.org/docs/Passes.html#sccp-sparse-conditional-constant-propagation>`_.

   .. function:: add_sroa_pass()

      See `scalarrepl pass documentation <http://llvm.org/docs/Passes.html#scalarrepl-scalar-replacement-of-aggregates>`_.

      Note that while the link above describes the transformation performed by the pass
      added by this function, it corresponds to the ``opt -sroa`` command-line option
      and not ``opt -scalarrepl``.

   .. function:: add_type_based_alias_analysis_pass()

   .. function:: add_basic_alias_analysis_pass()

      See `basicaa pass documentation <http://llvm.org/docs/AliasAnalysis.html#the-basicaa-pass>`_.

.. class:: ModulePassManager()

   Create a new pass manager to run optimization passes on a module.

   The following method is available:

   .. method:: run(module)

      Run optimization passes on the *module* (a :class:`ModuleRef` instance).
      True is returned if the optimizations made any modification to the
      module, False instead.


.. class:: FunctionPassManager(module)

   Create a new pass manager to run optimization passes on a function of
   the given *module* (an :class:`ModuleRef` instance).

   The following methods are available:

   .. method:: finalize()

      Run all the finalizers of the optimization passes.

   .. method:: initialize()

      Run all the initializers of the optimization passes.

   .. method:: run(function)

      Run optimization passes on the *function* (a :class:`ValueRef` instance).
      True is returned if the optimizations made any modification to the
      module, False instead.
