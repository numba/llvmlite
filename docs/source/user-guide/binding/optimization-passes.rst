===================
Optimization passes
===================

.. currentmodule:: llvmlite.binding

LLVM gives you the opportunity to fine-tune optimization passes.  Optimization
passes are managed by a pass manager. There are two kinds of pass managers:

* :class:`FunctionPassManager`, for optimizations that work on
  single functions.

* :class:`ModulePassManager`, for optimizations that work on
  whole modules.

llvmlite provides bindings for LLVM's *New* and *Legacy* pass managers, which
have slightly different APIs and behaviour. The differences between them and the
motivations for the New Pass Manager are outlined in the `LLVM Blog post on the
New Pass Manager
<https://blog.llvm.org/posts/2021-03-26-the-new-pass-manager/>`_.

In a future version of llvmlite, likely coinciding with a minimum LLVM version
requirement of 17, support for the Legacy Pass Manager will be removed. It is
recommended that new code using llvmlite uses the New Pass Manager, and existing
code using the Legacy Pass Manager be updated to use the New Pass Manager.


New Pass Manager APIs
=====================

To manage the optimization attributes we first need to instantiate a
:class:`PipelineTuningOptions` instance:

.. class:: PipelineTuningOptions(speed_level=2, size_level=0)
   
   Creates a new PipelineTuningOptions object.

   The following writable attributes are available, whose default values depend
   on the initial setting of the speed and size optimization levels:

   * .. attribute:: loop_interleaving

        Enable loop interleaving.

   * .. attribute:: loop_vectorization

        Enable loop vectorization.

   * .. attribute:: slp_vectorization

        Enable SLP vectorization, which uses a different algorithm to
        loop vectorization. Both may be enabled at the same time.

   * .. attribute:: loop_unrolling

        Enable loop unrolling.

   * .. attribute:: speed_level

        The level of optimization for speed, as an integer between 0 and 3.

   * .. attribute:: size_level

        The level of optimization for size, as an integer between 0 and 2.

.. FIXME: Available from llvm16
.. * .. attribute:: inlining_threshold

..      The integer threshold for inlining one function into
..      another. The higher the number, the more likely that
..      inlining will occur. This attribute is write-only.


We also need a :class:`PassBuilder` object to manage the respective function
and module pass managers:

.. class:: PassBuilder(target_machine, pipeline_tuning_options)
   
   A pass builder that uses the given :class:`TargetMachine` and
   :class:`PipelineTuningOptions` instances.

   .. method:: getModulePassManager()
    
      Return a populated :class:`ModulePassManager` object based on PTO settings.

   .. method:: getFunctionPassManager()
    
      Return a populated :class:`FunctionPassManager` object based on PTO
      settings.


The :class:`ModulePassManager` and :class:`FunctionPassManager` classes
implement the module and function pass managers:

.. class:: ModulePassManager()

   A pass manager for running optimization passes on an LLVM module.

   .. method:: add_verifier()

      Add the `Module Verifier
      <https://llvm.org/docs/Passes.html#verify-module-verifier>`_ pass.

   .. method:: run(module, passbuilder)
    
      Run optimization passes on *module*, a :class:`ModuleRef` instance.


.. class:: FunctionPassManager()

   A pass manager for running optimization passes on an LLVM function.

   .. method:: run(function, passbuilder)
  
      Run optimization passes on *function*, a :class:`ValueRef` instance.


These can be created with passes populated by using the
:meth:`PassBuilder.getModulePassManager` and
:meth:`PassBuilder.getFunctionPassManager` methods, or they can be instantiated
unpopulated, then passes can be added using the ``add_*`` methods.

To instantiate the unpopulated instances, use:

.. function:: create_new_module_pass_manager()

   Create an unpopulated :class:`ModulePassManager` instance.

and

.. function:: create_new_function_pass_manager()

   Create an unpopulated :class:`FunctionPassManager` instance.


The ``add_*`` methods supported by both pass manager classes are:

.. currentmodule:: None

.. method:: add_aa_eval_pass()

   Add the `Exhaustive Alias Analysis Precision Evaluator
   <https://llvm.org/docs/Passes.html#aa-eval-exhaustive-alias-analysis-precision-evaluator>`_
   pass.

.. method:: add_loop_unroll_pass()

   Add the `Loop Unroll
   <https://llvm.org/docs/Passes.html#loop-unroll-unroll-loops>`_ pass.

.. method:: add_loop_rotate_pass()

   Add the `Loop Rotate
   <https://llvm.org/docs/Passes.html#loop-rotate-rotate-loops>`_ pass.

.. method:: add_instruction_combine_pass()

   Add the `Combine Redundant Instructions
   <https://llvm.org/docs/Passes.html#instcombine-combine-redundant-instructions>`_
   pass.

.. method:: add_jump_threading_pass()

   Add the `Jump Threading
   <https://llvm.org/docs/Passes.html#jump-threading-jump-threading>`_ pass.

.. method:: add_simplify_cfg_pass()

   Add the `Simplify CFG
   <https://llvm.org/docs/Passes.html#simplifycfg-simplify-the-cfg>`_ pass.

.. method:: add_refprune_pass()

   Add the `Reference pruning
   <https://github.com/numba/llvmlite/blob/main/ffi/custom_passes.cpp>`_ pass.

.. currentmodule:: llvmlite.binding

Legacy Pass Manager APIs
========================

To instantiate either of these pass managers, you first need to
create and configure a :class:`PassManagerBuilder`.

.. class:: PassManagerBuilder()

   Create a new pass manager builder. This object centralizes
   optimization settings.

   The ``populate`` method is available:

   .. method:: populate(pm)

      Populate the pass manager *pm* with the optimization passes
      configured in this pass manager builder.

   The following writable attributes are available:

   * .. attribute:: disable_unroll_loops

        If ``True``, disable loop unrolling.

   * .. attribute:: inlining_threshold

        The integer threshold for inlining one function into
        another. The higher the number, the more likely that
        inlining will occur. This attribute is write-only.

   * .. attribute:: loop_vectorize

        If ``True``, allow vectorizing loops.

   * .. attribute:: opt_level

        The general optimization level, as an integer between 0
        and 3.

   * .. attribute:: size_level

        Whether and how much to optimize for size, as an integer
        between 0 and 2.

   * .. attribute:: slp_vectorize

        If ``True``, enable the SLP vectorizer, which uses a
        different algorithm than the loop vectorizer. Both may
        be enabled at the same time.


.. class:: PassManager

   The base class for pass managers. Use individual ``add_*``
   methods or :meth:`PassManagerBuilder.populate` to add
   optimization passes.

   * .. function:: add_constant_merge_pass()

        See `constmerge pass documentation <http://llvm.org/docs/Passes.html#constmerge-merge-duplicate-global-constants>`_.

   * .. function:: add_dead_arg_elimination_pass()

        See `deadargelim pass documentation <http://llvm.org/docs/Passes.html#deadargelim-dead-argument-elimination>`_.

   * .. function:: add_function_attrs_pass()

        See `functionattrs pass documentation <http://llvm.org/docs/Passes.html#functionattrs-deduce-function-attributes>`_.

   * .. function:: add_function_inlining_pass(self, )

        See `inline pass documentation <http://llvm.org/docs/Passes.html#inline-function-integration-inlining>`_.

   * .. function:: add_global_dce_pass()

        See `globaldce pass documentation <http://llvm.org/docs/Passes.html#globaldce-dead-global-elimination>`_.

   * .. function:: add_global_optimizer_pass()

        See `globalopt pass documentation <http://llvm.org/docs/Passes.html#globalopt-global-variable-optimizer>`_.

   * .. function:: add_ipsccp_pass()

        See `ipsccp pass documentation <http://llvm.org/docs/Passes.html#ipsccp-interprocedural-sparse-conditional-constant-propagation>`_.

   * .. function:: add_dead_code_elimination_pass()

        See `dce pass documentation <http://llvm.org/docs/Passes.html#dce-dead-code-elimination>`_.

   * .. function:: add_cfg_simplification_pass()

        See `simplifycfg pass documentation <http://llvm.org/docs/Passes.html#simplifycfg-simplify-the-cfg>`_.

   * .. function:: add_gvn_pass()

        See `gvn pass documentation <http://llvm.org/docs/Passes.html#gvn-global-value-numbering>`_.

   * .. function:: add_instruction_combining_pass()

        See `instcombine pass documentation <http://llvm.org/docs/Passes.html#passes-instcombine>`_.

   * .. function:: add_licm_pass()

        See `licm pass documentation <http://llvm.org/docs/Passes.html#licm-loop-invariant-code-motion>`_.

   * .. function:: add_sccp_pass()

        See `sccp pass documentation <http://llvm.org/docs/Passes.html#sccp-sparse-conditional-constant-propagation>`_.

   * .. function:: add_sroa_pass()

        See `scalarrepl pass documentation <http://llvm.org/docs/Passes.html#scalarrepl-scalar-replacement-of-aggregates>`_.

        While the scalarrepl pass documentation describes the
        transformation performed by the pass added by this
        function, the pass corresponds to the ``opt -sroa``
        command-line option and not to ``opt -scalarrepl``.

   * .. function:: add_type_based_alias_analysis_pass()

        See `tbaa metadata documentation <http://llvm.org/docs/LangRef.html#tbaa-metadata>`_.

   * .. function:: add_basic_alias_analysis_pass()

        See `basicaa pass documentation <http://llvm.org/docs/AliasAnalysis.html#the-basicaa-pass>`_.

   * .. function:: add_instruction_namer_pass()

        See `instnamer pass documentation <http://llvm.org/docs/Passes.html#instnamer-assign-names-to-anonymous-instructions>`_.

   * .. function:: add_refprune_pass()

     Add the `Reference pruning
     <https://github.com/numba/llvmlite/blob/main/ffi/custom_passes.cpp>`_ pass.

.. class:: ModulePassManager()
   :no-index:

   Create a new pass manager to run optimization passes on a
   module.

   The ``run`` method is available:

   .. method:: run(module)
      :no-index:

      Run optimization passes on the
      *module*, a :class:`ModuleRef` instance.

      Returns ``True`` if the optimizations made any modification
      to the module. Otherwise returns ``False``.

.. class:: FunctionPassManager(module)
   :no-index:

   Create a new pass manager to run optimization passes on a
   function of the given *module*, a :class:`ModuleRef` instance.

   The following methods are available:

   * .. method:: finalize()

        Run all the finalizers of the optimization passes.

   * .. method:: initialize()

        Run all the initializers of the optimization passes.

   * .. method:: run(function)
        :no-index:

        Run optimization passes on *function*, a
        :class:`ValueRef` instance.

        Returns ``True`` if the optimizations made any
        modification to the module. Otherwise returns ``False``.
