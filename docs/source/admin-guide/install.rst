==============
Installation
==============

Contrary to what you might expect, llvmlite does *not* use any LLVM shared
libraries that may be present on the system, or in the conda environment.  The
parts of LLVM required by llvmlite are statically linked at build time.  As a
result, installing llvmlite from a binary package does not also require the
end user to install LLVM.  (For more details on the reasoning behind this,
see: :ref:`why-static`)

Pre-built binaries
==================

Building LLVM for llvmlite is challenging, so we *strongly* recommend
installing a binary package where we have built and tested everything for you.
Official conda packages are available in the Anaconda_ distribution::

    conda install llvmlite

Development releases are built from the Git master branch and uploaded to
the Numba_ channel on `Anaconda Cloud <https://anaconda.org/numba>`_::

    conda install --channel numba llvmlite

Binary wheels are also available for installation from PyPI_::

    pip install llvmlite


Building manually
=================

Building llvmlite requires first building LLVM.  Do not use prebuilt LLVM
binaries from your OS distribution or the LLVM website!  There will likely be
a mismatch in version or build options, and LLVM will be missing certain patches
that are critical for llvmlite operation.

Prerequisites
-------------

Before building, you must have the following:

* On Windows:

  * Visual Studio 2015 (Update 3) or later, to compile LLVM and llvmlite.
    The free Express edition is acceptable.

  * CMake_ installed.

* On Linux:

  * g++ (>= 4.8) and CMake_

  * If building LLVM on Ubuntu, the linker may report an error
    if the development version of ``libedit`` is not installed. If
    you run into this problem, install ``libedit-dev``.

* On Mac:

  * Xcode for the compiler tools, and CMake_


Compiling LLVM
--------------

If you can build llvmlite inside a conda environment, you can install a
prebuilt LLVM binary package and skip this step::

    conda install -c numba llvmdev

The LLVM build process is fully scripted by conda-build_, and the `llvmdev recipe <https://github.com/numba/llvmlite/tree/master/conda-recipes/llvmdev>`_ is the canonical reference for building LLVM for llvmlite.  Please use it if at all possible!

The manual instructions below describe the main steps, but refer to the recipe for details:

#. Download the `LLVM 7.0.0 source code <http://releases.llvm.org/7.0.0/llvm-7.0.0.src.tar.xz>`_.

#. Download or git checkout the `llvmlite source code <https://github.com/numba/llvmlite>`_.

#. Decompress the LLVM tar file and apply the following patches from the ``llvmlite/conda-recipes/`` directory:

    #. ``llvm-lto-static.patch``: Fix issue with LTO shared library on Windows
    #. ``D47188-svml-VF.patch``: Add support for vectorized math functions via Intel SVML
    #. ``partial-testing.patch``: Enables additional parts of the LLVM test suite
    #. ``twine_cfg_undefined_behavior.patch``: Fix obscure memory corruption bug in LLVM that hasn't been fixed in master yet
    #. ``0001-RuntimeDyld-Fix-a-bug-in-RuntimeDyld-loadObjectImpl-.patch``: Fixes a bug relating to common symbol section size computation
    #. ``0001-RuntimeDyld-Add-test-case-that-was-accidentally-left.patch``: Test for the above patch

#. For Linux/macOS:
    #. ``export PREFIX=desired_install_location CPU_COUNT=N`` (``N`` is number of parallel compile tasks)
    #. Run the `build.sh <https://github.com/numba/llvmlite/blob/master/conda-recipes/llvmdev/build.sh>`_ script in the llvmdev conda recipe from the LLVM source directory

#. For Windows:
    #. ``set PREFIX=desired_install_location``
    #. Run the `bld.bat <https://github.com/numba/llvmlite/blob/master/conda-recipes/llvmdev/bld.bat>`_ script in the llvmdev conda recipe from the LLVM source directory.


Compiling llvmlite
------------------

#. To build the llvmlite C wrapper, which embeds a statically
   linked copy of the required subset of LLVM, run the following from the llvmlite source directory::

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


.. _why-static:

Why Static Linking to LLVM?
===========================

The llvmlite package uses LLVM via ctypes calls to a C wrapper that is
statically linked to LLVM.  Some people are surprised that llvmlite uses
static linkage to LLVM, but there are several important reasons for this:

#. *The LLVM API has not historically been stable across releases* - Although
   things have improved since LLVM 4.0, there are still enough changes between
   LLVM releases to cause compilation issues if the right version is not
   matched with llvmlite.

#. *The LLVM shipped by most Linux distributions is not the version
   llvmlite needs* - The release cycles of Linux distributions will never line
   up with LLVM or llvmlite releases.

#. *We need to patch LLVM* - The binary packages of llvmlite are built
   against LLVM with a handful of patches to either fix bugs or to add
   features that have not yet been merged upstream.  In some cases, we've had
   to carry patches for several releases before they make it into LLVM.

#. *We don't need most of LLVM* - We are sensitive to the install size of
   llvmlite, and a full build of LLVM is quite large.  We can dramatically
   reduce the total disk needed by an llvmlite user (who typically doesn't
   need the rest of LLVM, ignoring the version matching issue) by statically
   linking to the library and pruning the symbols we do not need.

#. *Numba can use multiple LLVM builds at once* - Some Numba targets (AMD GPU,
   for example) may require different LLVM versions or non-mainline forks of
   LLVM to work.  These other LLVMs can be wrapped in a similar fashion as
   llvmlite, and will stay isolated.

#. *We need to support Windows + Python 2.7* - Python 2.7 extensions on
   Windows needs to be built with Visual Studio 2008 for ABI compatibility
   reasons.  This presents a serious issue as VS2008 can no longer build LLVM.
   The best workaround we have found (until the sunset of Python 2.7) is to
   build LLVM and the llvmlite C wrapper with VS2015 and call it through
   ctypes.  This is not ideal, but experience has shown it seems to work.

Static linkage of LLVM was definitely not our goal early in Numba development,
but seems to have become the only workable solution given our constraints.

.. _CMake: http://www.cmake.org/
.. _Numba: http://numba.pydata.org/
.. _PyPI: https://pypi.org/project/llvmlite/
.. _Conda: https://conda.io/docs/
.. _conda-build: https://conda.io/docs/user-guide/tasks/build-packages/index.html
.. _Anaconda: http://docs.continuum.io/anaconda/index.html
