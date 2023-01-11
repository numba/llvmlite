.. _binding-layer:

=====================================
LLVM binding layer---llvmlite.binding
=====================================

.. module:: llvmlite.binding
   :synopsis: Interacting with the LLVM library.

The :mod:`llvmlite.binding` module provides classes to interact
with functionalities of the LLVM library. Generally, they closely
mirror concepts of the C++ API. Only a small subset of the LLVM
API is mirrored: those parts that have proven useful to
implement Numba_'s JIT compiler.

.. _Numba: http://numba.pydata.org/


.. toctree::
   :maxdepth: 1

   initialization-finalization
   dynamic-libraries
   target-information
   context
   modules
   value-references
   type-references
   execution-engine
   object-file
   optimization-passes
   analysis-utilities
   pass_timings
   misc
   examples

