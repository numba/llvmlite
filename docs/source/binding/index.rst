
.. _binding-layer:

llvmlite.binding -- The LLVM binding layer
==========================================

.. module:: llvmlite.binding
   :synopsis: Interacting with the LLVM library.


The :mod:`llvmlite.binding` module provides classes to interact with
functionalities of the LLVM library.  They generally mirror concepts of
the C++ API closely.  A small subset of the LLVM API is mirrored, though:
only those parts that have proven useful to implement Numba_'s JIT compiler.


.. _Numba: http://numba.pydata.org/

.. toctree::
   :maxdepth: 3

   initfini.rst
   dylib.rst
   targets.rst
   modules.rst
   values.rst
   engine.rst
   passmanager.rst
   analysis.rst
   examples.rst



