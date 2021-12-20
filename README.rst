========
llvmlite
========

.. image:: https://dev.azure.com/numba/numba/_apis/build/status/numba.llvmlite?branchName=master
   :target: https://dev.azure.com/numba/numba/_build/latest?definitionId=2&branchName=master
   :alt: Azure Pipelines
.. image:: https://codeclimate.com/github/numba/llvmlite/badges/gpa.svg
   :target: https://codeclimate.com/github/numba/llvmlite
   :alt: Code Climate
.. image:: https://coveralls.io/repos/github/numba/llvmlite/badge.svg
   :target: https://coveralls.io/github/numba/llvmlite
   :alt: Coveralls.io
.. image:: https://readthedocs.org/projects/llvmlite/badge/
   :target: https://llvmlite.readthedocs.io
   :alt: Readthedocs.io

A Lightweight LLVM Python Binding for Writing JIT Compilers
-----------------------------------------------------------

.. _llvmpy: https://github.com/llvmpy/llvmpy

llvmlite is a project originally tailored for Numba_'s needs, using the
following approach:

* A small C wrapper around the parts of the LLVM C++ API we need that are
  not already exposed by the LLVM C API.
* A ctypes Python wrapper around the C API.
* A pure Python implementation of the subset of the LLVM IR builder that we
  need for Numba.

Why llvmlite
============

The old llvmpy_  binding exposes a lot of LLVM APIs but the mapping of
C++-style memory management to Python is error prone. Numba_ and many JIT
compilers do not need a full LLVM API.  Only the IR builder, optimizer,
and JIT compiler APIs are necessary.

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

llvmlite works with Python 3.7 and greater.

As of version 0.37.0, llvmlite requires LLVM 11.x.x on all architectures

Historical compatibility table:

=================  ========================
llvmlite versions  compatible LLVM versions
=================  ========================
0.37.0 - ...       11.x.x
0.34.0 - 0.36.0    10.0.x (9.0.x for  ``aarch64`` only)
0.33.0             9.0.x
0.29.0 - 0.32.0    7.0.x, 7.1.x, 8.0.x
0.27.0 - 0.28.0    7.0.x
0.23.0 - 0.26.0    6.0.x
0.21.0 - 0.22.0    5.0.x
0.17.0 - 0.20.0    4.0.x
0.16.0 - 0.17.0    3.9.x
0.13.0 - 0.15.0    3.8.x
0.9.0 - 0.12.1     3.7.x
0.6.0 - 0.8.0      3.6.x
0.1.0 - 0.5.1      3.5.x
=================  ========================

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
