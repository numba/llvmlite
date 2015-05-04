
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

