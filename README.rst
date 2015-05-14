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


Documentation
=============

You'll find the documentation at http://llvmlite.pydata.org


Dependencies
============

You need Python 2.6 or greater (including Python 3.3 or greater).

Build dependencies
------------------

- LLVM 3.5
- A C++ 11 compiler, and possibly other tools (see below)

Runtime dependencies
--------------------

- For Python versions before 3.4, the enum34_ package is required

.. _enum34: https://pypi.python.org/pypi/enum34


Pre-built binaries
==================

We recommend you use the binaries provided by the Numba_ team for
the Conda_ package manager.  You can find them in Numba's `binstar
channel <https://binstar.org/numba>`.  For example::

   $ conda install --channel=numba llvmlite

(or, simply, the official llvmlite package provided in the Anaconda_
distribution)

.. _Numba: http://numba.pydata.org/
.. _Conda: http://conda.pydata.org/
.. _Anaconda: http://docs.continuum.io/anaconda/index.html


Build
=====

This section applies if you don't want to use the pre-built binaries.

Run ``python setup.py build``.  This builds the llvmlite C wrapper,
which contains a statically-linked copy of the required subset of LLVM.

If your LLVM is installed in a non-standard location, first point the
``LLVM_CONFIG`` environment variable to the path of the corresponding
``llvm-config`` (or ``llvm-config.exe``) executable.

Unix requirements
-----------------

You must have a LLVM 3.5 build (libraries and header files) available
somewhere.  Under Ubuntu 14.10 and Debian unstable, you can install
``llvm-3.5-dev``.  Versions shipped with some earlier distributions such as
Ubuntu 14.04 are known to be broken.

When building on Ubuntu, the linker may report an error if the development
version of ``libedit`` is not installed. Install ``libedit-dev`` if you
run into this problem.

Windows requirements
--------------------

You must have Visual Studio 2012 or later (the free "Express" edition is ok).
In addition, you must have cmake_ installed, and LLVM should have been
built using cmake, in Release mode.  Be careful to use the right bitness
(32- or 64-bit) for your Python installation.

.. _cmake: http://www.cmake.org/

Run tests
---------

Run ``python runtests.py`` or ``python -m llvmlite.tests``.

Install
-------

Run ``python setup.py install``.
