
Introduction
============

Overview
--------

llvmlite is born of the desire to have a new Python binding to LLVM for
use in Numba_.  Numba used to rely on llvmpy_, but llvmpy became harder
and harder to maintain, because of its cumbersome architecture and also
because the C++11 requirement of recent LLVM versions don't go well with
the compiler and runtime ABI requirements of some Python versions
(especially under Windows).

Moreover, llvmpy proved to be responsible for a sizable chunk of Numba's
compilation times, because of its inefficient layering and object
encapsulation.  Fixing this issue inside the llvmpy codebase seemed
a time-consuming and uncertain task.

Therefore, the Numba developers decided to start a new binding from scratch,
with an entire different architecture, centered around the specific
requirements of a JIT compiler.

.. _Numba: http://numba.pydata.org/
.. _llvmpy: http://www.llvmpy.org/

Philosophy
----------

While llvmpy_ exposed large parts of the LLVM C++ API for direct calls
into the LLVM library, llvmlite takes an entirely different approach.
llvmlite starts from the needs of a JIT compiler and splits them into
two decoupled tasks:

1. Construction of a :term:`module`, function by function,
   :term:`instruction` by instruction
2. Compilation and optimization of the module into machine code

The construction of a LLVM module doesn't call the LLVM C++ API; rather,
it constructs the LLVM :term:`Intermediate Representation` in pure Python.
This is the part of the :ref:`IR layer <ir-layer>`.

The compilation of a LLVM module takes the IR in textual form and feeds
it into LLVM's parsing API.  It then returns a thin wrapper around
LLVM's C++ module object.  This is the part of the
:ref:`binding layer <binding-layer>`.

Once parsed, the module's source code cannot be modified anymore; this
is where llvmlite loses in flexibility compared to the direct mapping
of C++ APIs into Python that was provided by llvmpy.  The saving in
maintenance effort, however, is large.

LLVM compatibility
------------------

Despite minimizing the API surface with LLVM, llvmlite is impacted
by changes to LLVM's C++ API (which can occur at every feature release).
Therefore, each llvmlite version is targetted to a specific LLVM feature
version.  It should work accross all given bugfix releases of that version
(for example, llvmlite 0.12.0 would work with LLVM 3.8.0 and 3.8.1, but
with neither LLVM 3.7.0 nor 3.9.0).

Which LLVM version is supported is driven by Numba_'s requirements.

API stability
-------------

At this time, we reserve ourselves the possibility to slightly break the
llvmlite API at each release.  This is necessary because of changes in
LLVM behaviour (for example differences in the IR accross versions), and
because llvmlite as a young library still has room for improvement or
fixes to the existing APIs.
