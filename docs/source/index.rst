========
llvmlite
========

:emphasis:`A lightweight LLVM-Python binding for writing JIT compilers`

llvmlite provides a Python binding to LLVM for use in Numba_. Numba
previously relied on llvmpy_.

Llvmpy became hard to maintain because:

* It has a cumbersome architecture.
* The C++11 requirement of recent LLVM versions does not go well
  with the compiler and runtime ABI requirements of some Python
  versions, especially under Windows.

Llvmpy also proved to be responsible for a sizable part of
Numba's compilation times, because of its inefficient layering
and object encapsulation. Fixing this issue inside the llvmpy
codebase seemed a time-consuming and uncertain task.

The Numba developers decided to start a new binding from scratch,
with an entirely different architecture, centered around the
specific requirements of a JIT compiler.

.. _Numba: http://numba.pydata.org/
.. _llvmpy: http://www.llvmpy.org/

Philosophy
==========

While llvmpy_ exposed large parts of the LLVM C++ API for direct
calls into the LLVM library, llvmlite takes an entirely different
approach. Llvmlite starts from the needs of a JIT compiler and
splits them into two decoupled tasks:

* Construction of a :ref:`module`, function by function,
  :ref:`instruction` by instruction.

* Compilation and optimization of the module into machine code.

The construction of an LLVM module does not call the LLVM C++ API.
Rather, it constructs the
LLVM :ref:`intermediate representation <intermediate representation>`
(IR) in pure Python. This is the role of the
:ref:`IR layer <ir-layer>`.

The compilation of an LLVM module takes the IR in textual form
and feeds it into LLVM's parsing API. It then returns a thin
wrapper around LLVM's C++ module object. This is the role of the
:ref:`binding layer <binding-layer>`.

Once parsed, the module's source code cannot be modified, which
loses the flexibility of the direct mapping of C++ APIs into
Python that was provided by llvmpy but saves a great deal of
maintenance.

LLVM compatibility
==================

Despite minimizing the API surface with LLVM, llvmlite is
impacted by changes to LLVM's C++ API, which can occur at every
feature release. Therefore, each llvmlite version is targeted to
a specific LLVM feature version and works across all given bugfix
releases of that version.

EXAMPLE: Llvmlite 0.12.0 works with LLVM 3.8.0 and 3.8.1, but
it does not work with LLVM 3.7.0 or 3.9.0.

Numba's requirements determine which LLVM version is supported.

API stability
=============

At this time, we reserve the possibility of slightly breaking
the llvmlite API at each release, for the following reasons:

* Changes in LLVM behaviour, such as differences in the IR across
  versions.

* As a young library, llvmlite has room for improvement or fixes
  to the existing APIs.


.. toctree::
   :maxdepth: 1
   :hidden:

   admin-guide/install
   user-guide/index
   faqs
   contributing
   release-notes
   glossary

.. |reg| unicode:: U+000AE .. REGISTERED SIGN
