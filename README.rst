========
llvmlite
========

A lightweight LLVM python binding for writing JIT compilers

The old llvmpy_  binding exposes a lot of LLVM APIs but the mapping of
C++-style memory management to Python is error prone. Numba_ and many JIT
compilers do not need a full LLVM API.  Only the IR builder, optimizer,
and JIT compiler APIs are necessary.

.. _llvmpy: https://github.com/llvmpy/llvmpy

llvmlite is a project originally tailored for Numba_'s needs, using the
following approach:

* A small C wrapper around the parts of the LLVM C++ API we need that are
  not already exposed by the LLVM C API.
* A ctypes Python wrapper around the C API.
* A pure Python implementation of the subset of the LLVM IR builder that we
  need for Numba.


Key Benefits
============

* The IR builder is pure Python code and decoupled from LLVM's
  frequently-changing C++ APIs.
* Materializing a LLVM module calls LLVM's IR parser which provides
  better error messages than step-by-step IR building through the C++
  API (no more segfaults or process aborts).
* Most of llvmlite uses the LLVM C API which is small but very stable
  (low maintenance when changing LLVM version).
* The binding is not a Python C-extension, but a plain DLL accessed using
  ctypes (no need to wrestle with Python's compiler requirements and C++ 11
  compatibility).
* The Python binding layer has sane memory management.
* llvmlite is quite faster than llvmpy's thanks to a much simpler architeture
  (the Numba_ test suite is twice faster than it was).

llvmpy Compatibility Layer
--------------------------

The ``llvmlite.llvmpy`` namespace provides a minimal llvmpy compatibility
layer.


Compatibility
=============

llvmlite works with Python 2.7 and Python 3.4 or greater.

As of version 0.10, llvmlite requires LLVM 3.7.  It does not support earlier
or later versions of LLVM.

Documentation
=============

You'll find the documentation at http://llvmlite.pydata.org


Pre-built binaries
==================

We recommend you use the binaries provided by the Numba_ team for
the Conda_ package manager.  You can find them in Numba's `anaconda.org
channel <https://anaconda.org/numba>`_.  For example::

   $ conda install --channel=numba llvmlite

(or, simply, the official llvmlite package provided in the Anaconda_
distribution)

.. _Numba: http://numba.pydata.org/
.. _Conda: http://conda.pydata.org/
.. _Anaconda: http://docs.continuum.io/anaconda/index.html


Other build methods
===================

If you don't want to use our pre-built packages, you can compile
and install llvmlite yourself.  The documentation will teach you how:
http://llvmlite.pydata.org/en/latest/install/index.html
