.. _ir-layer:

======================
IR layer---llvmlite.ir
======================

.. module:: llvmlite.ir
   :synopsis: Classes for building the LLVM intermediate representation of functions.

The :mod:`llvmlite.ir` module contains classes and utilities to
build the LLVM
:ref:`intermediate representation <intermediate representation>`
(IR) of native functions.

The provided APIs may sometimes look like LLVM's C++ APIs, but
they never call into LLVM, unless otherwise noted. Instead, they
construct a pure Python representation of the IR.

To use this module, you should be familiar with the concepts
in the `LLVM Language Reference
<https://releases.llvm.org/10.0.0/docs/LangRef.html>`_.

.. toctree::
   :maxdepth: 1

   types
   values
   modules
   ir-builder
   examples
