
.. _ir-layer:

llvmlite.ir -- The IR layer
===========================

.. module:: llvmlite.ir
   :synopsis: Classes for building the LLVM Intermediate Representation of functions.


The :mod:`llvmlite.ir` module contains classes and utilities to build
the LLVM :term:`Intermediate Representation` of native functions.  The
provided APIs may sometimes look like LLVM's C++ APIs, but they never call
into LLVM (unless otherwise noted): they construct a pure Python
representation of the :term:`IR`.

.. seealso::
   To make use of this module, you should be familiar with the concepts
   presented in the `LLVM Language Reference
   <http://llvm.org/releases/3.8.0/docs/LangRef.html>`_.

.. toctree::
   :maxdepth: 3

   types.rst
   values.rst
   modules.rst
   builder.rst
   examples.rst
