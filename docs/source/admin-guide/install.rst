==============
Installation
==============

Contrary to what you might expect, llvmlite does *not* use any LLVM shared
libraries that may be present on the system, or in the conda environment.  The
parts of LLVM required by llvmlite are statically linked at build time.  As a
result, installing llvmlite from a binary package does not also require the
end user to install LLVM.  (For more details on the reasoning behind this,
see: :ref:`faq_why_static`).

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

The manual instructions below describe the main steps, but refer to the recipe
for details:

#. Download the `LLVM 9.0.1 source code <https://github.com/llvm/llvm-project/releases/download/llvmorg-9.0.1/llvm-9.0.1.src.tar.xz>`_.

#. Download or git checkout the `llvmlite source code <https://github.com/numba/llvmlite>`_.

#. Decompress the LLVM tar file and apply the following patches from the
   ``llvmlite/conda-recipes/`` directory.  You can apply each patch using the
   Linux ``patch -p1 -i {patch-file}`` command:

    #. ``llvm-lto-static.patch``: Fix issue with LTO shared library on Windows
    #. ``partial-testing.patch``: Enables additional parts of the LLVM test
       suite
    #. ``intel-D47188-svml-VF.patch``: Add support for vectorized math
       functions via Intel SVML.
    #. ``0001-Revert-Limit-size-of-non-GlobalValue-name.patch``: revert the
       limit put on the length of a non-GlobalValue name

#. For Linux/macOS:
    #. ``export PREFIX=desired_install_location CPU_COUNT=N`` (``N`` is number
       of parallel compile tasks)
    #. Run the `build.sh <https://github.com/numba/llvmlite/blob/master/conda-recipes/llvmdev/build.sh>`_
       script in the llvmdev conda recipe from the LLVM source directory

#. For Windows:
    #. ``set PREFIX=desired_install_location``
    #. Run the `bld.bat <https://github.com/numba/llvmlite/blob/master/conda-recipes/llvmdev/bld.bat>`_
       script in the llvmdev conda recipe from the LLVM source directory.


Compiling llvmlite
------------------

#. To build the llvmlite C wrapper, which embeds a statically
   linked copy of the required subset of LLVM, run the following from the
   llvmlite source directory::

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

#. If you wish to build against an unsupported LLVM version, set the environment
   variable ``LLVMLITE_SKIP_LLVM_VERSION_CHECK`` to non-zero. Note that this is
   useful for e.g. testing new versions of llvmlite, but support for llvmlite
   built in this manner is limited/it's entirely possible that llvmlite will not
   work as expected. See also:
   :ref:`why llvmlite doesn’t always support the latest release(s) of LLVM<faq_supported_versions>`.


Installing
----------

#. To validate your build, run the test suite by running::

     python runtests.py

   or::

     python -m llvmlite.tests

#. If the validation is successful, install by running::

     python setup.py install

Installing from sdist
---------------------

If you don't want to do any modifications to llvmlite itself,
it's also possible to use ``pip`` to compile and install llvmlite
from the latest released sdist package.
You'll still need to point to your ``llvm-config`` if it's not in the ``PATH``:

``LLVM_CONFIG=/path/to/llvm-config pip3 install llvmlite``

This should work on any platform that runs Python and llvm.
It has been observed to work on ``arm``, ``ppc64le``,
and also ``pypy3`` on ``arm``.

x86 users will need to pass an extra flag (see
`issue \#522 <https://github.com/numba/llvmlite/issues/522>`_):

``LLVM_CONFIG=/path/to/llvm-config CXXFLAGS=-fPIC pip3 install llvmlite``

This is known to work with ``pypy3`` on ``Linux x64``.

It's also possible to force ``pip`` to rebuild ``llvmlite`` locally with
a custom version of ``llvm`` :

``LLVM_CONFIG=/path/to/custom/llvm-config CXXFLAGS=-fPIC pip3 install --no-binary :all: llvmlite``


.. _CMake: http://www.cmake.org/
.. _Numba: http://numba.pydata.org/
.. _PyPI: https://pypi.org/project/llvmlite/
.. _Conda: https://conda.io/docs/
.. _conda-build: https://conda.io/docs/user-guide/tasks/build-packages/index.html
.. _Anaconda: http://docs.continuum.io/anaconda/index.html
