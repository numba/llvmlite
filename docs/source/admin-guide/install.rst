==============
Installation
==============

For your convenience, you can install llvmlite using the pre-built
binaries provided for the conda_ package manager.

If do not want to use conda or if you modified llvmlite yourself,
you need to build it manually.

Pre-built binaries
==================

Official binaries are available in the Anaconda_\ |reg| distribution.

* To install the pre-built binaries, run::

     conda install llvmlite

* To obtain a more recent version, fetch the automatic builds
  from the Numba_ `Anaconda Cloud channel <https://anaconda.org/numba>`_::

     conda install --channel numba llvmlite


Building manually
=================

Prerequisites
-------------

Before building, you must have the following:

* On Windows:

  * Visual Studio 2015 or later, to compile LLVM and llvmlite.
    The free Express edition is acceptable.

  * CMake_ installed.

  * LLVM built using CMake in Release mode.

  Be sure to use the correct bit format---either 32-bit or
  64-bit---for your Python installation.

* On Unix:

  * An LLVM 6.0 build---libraries and header files---available
    somewhere.

  * On recent Ubuntu or Debian systems, you may install the
    ``llvm-6.0-dev`` package, if it is available.

  * If building LLVM on Ubuntu, the linker may report an error
    if the development version of ``libedit`` is not installed. If
    you run into this problem, install ``libedit-dev``.


Compiling
----------

#. To build the llvmlite C wrapper, which embeds a statically
   linked copy of the required subset of LLVM, run::

     python setup.py build

#. If your LLVM is installed in a nonstandard location, set the
   ``LLVM_CONFIG`` environment variable to the location of the
   corresponding ``llvm-config`` or ``llvm-config.exe``
   executable. This variable must persist into the installation
   of llvmlite---for example, into a Python environment.

   EXAMPLE: If LLVM is installed in ``/opt/llvm/`` with the
   ``llvm-config`` binary located at
   ``/opt/llvm/bin/llvm-config``, set
   ``LLVM_CONFIG=/opt/llvm/bin/llvm-config``.


Installing
----------

#. To validate your build, run the test suite by running::

     python runtests.py

   or::

     python -m llvmlite.tests

#. If the validation is successful, install by running::

     python setup.py install


.. _CMake: http://www.cmake.org/
.. _Numba: http://numba.pydata.org/
.. _Conda: http://conda.pydata.org/
.. _Anaconda: http://docs.continuum.io/anaconda/index.html

.. |reg| unicode:: U+000AE .. REGISTERED SIGN
