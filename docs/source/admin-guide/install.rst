==============
Installation
==============

The Numba/llvmlite stack consists of the following major components:

* *Numba* is the compiler package, this depends on llvmlite.
* *llvmlite* is a lightweight binding package to the LLVM APIs, it depends on LLVM.
* *LLVM*  is the JIT compiler framework for producing executable code from various
  inputs.

All components must be compiled in order to be used. And, since each component
on the stack depends on the previous one, you need to compile LLVM in order to
compile llvmlite in order to compile Numba. The LLVM package is a significant
size and may take significant time (magnitude, roughly an hour) and skill to
compile depending on the platform.

Pre-built binaries
==================

As mentioned above, building LLVM for llvmlite is challenging. Installing a
binary package that has been built and tested is *strongly* recommend.

Official Conda packages are available in the Anaconda_ distribution::

    conda install llvmlite

Development releases are built from the Git master branch and uploaded to
the Numba_ development channel on `Anaconda Cloud <https://anaconda.org/numba>`_::

    conda install -c numba/label/dev llvmlite

Binary wheels are also available for installation from PyPI_::

    pip install llvmlite

Development releases of binary wheels are not made available.

Contrary to what might be expected, the llvmlite packages built by the Numba
maintainers do *not* use any LLVM shared libraries that may be present on the
system, and/or in the Conda environment. The parts of LLVM required by llvmlite
are statically linked at build time.  As a result, installing llvmlite from a
binary package from the Numba channel does not also require the end user to
install LLVM.  (For more
details on the reasoning behind this, see: :ref:`faq_why_static`). Note however
also that llvmlite packages compiled by other parties, e.g. conda-forge may
split this into and ``llvmlite`` and ``llvm`` package and link dynamically.

Conda packages:
---------------

The Numba maintainers ship to the Numba channel:

  * Numba packages
  * llvmlite packages
  * llvmdev packages (this contains a build of LLVM)

The llvmdev packages are not needed at runtime by llvmlite packages as
llvmlite's dynamic libraries are statically linked (see above) at compile time
against LLVM through the dependency on the ``llvmdev`` package.

The Anaconda distribution and conda-forge channels ship:

  * Numba packages
  * llvmlite packages
  * LLVM split into runtime libraries (package called ``llvm``) and compile time
    libraries/headers etc this contains a build of LLVM (package called
    ``llvmdev``)

At compile time the ``llvmdev`` and ``llvm`` packages are used to build llvmlite and
llvmlite's dynamic libraries are dynamically linked against the libraries in the
``llvm`` meta-package. This means at runtime ``llvmlite`` depends on the ``llvm``
package which has the LLVM shared libraries in it (it's actually a package
called ``libllvm`` that contains the DSOs, but the ``llvm`` package is referred to
so as to get the ``run_exports``).

Using ``pip``
-------------

The Numba maintainers ship binary wheels:

  * Numba wheels (``x86*`` architectures)
  * llvmlite wheels (``x86*`` architectures)

Note that the llvmlite wheels are statically linked against LLVM, as per the
conda packages on the Numba channel. This mitigates the need for a LLVM based
binary wheel. Note also that this, as of version 0.36, does not include the
``aarch64`` architectures, for example installation on a Raspberry Pi is not
supported.

The Numba maintainers ship an ``sdist`` for:

  * Numba
  * llvmlite

Note that there is no ``sdist`` provided for LLVM. If you try and build ``llvmlite``
from ``sdist`` you will need to bootstrap the package with your own appropriate
LLVM.

How this ends up being a problem.
.................................

1. If you are on an unsupported architecture (i.e. not ``x86*``) or unsupported
   Python version for binary wheels (e.g. Python alphas) then ``pip`` will try and
   build Numba from ``sdist`` which in turn will try and build ``llvmlite`` from
   ``sdist``. This will inevitably fail as the ``llvmlite`` source distribution
   needs an appropriate LLVM installation to build.
2. If you are using ``pip < 19.0`` then ``manylinux2010`` wheels will not
   install and you end up in the situation in 1. i.e. something unsupported so
   building from ``sdist``.

Historically, this issues has manifested itself as the following error
message, which included here verbatim for future reference::

    FileNotFoundError: [Errno 2] No such file or directory: 'llvm-config'

Things to "fix" it...
.....................

1. If you are using ``pip < 19.0`` and on ``x86*``, then update it if you can, this will
   let you use the ``manylinux2010`` binary wheels.

2. If you are on an unsupported architecture, for example Raspberry Pi, please
   use ``conda`` if you have that available.

3. Otherwise: you will probably need to build from source, this means providing
   an LLVM. If you have conda available you could use this to bootstrap the
   installation with a working ``llvm``/``llvmdev`` package. Learn more about
   compiling from source in the section on `Building manually`_ below.
   and in particular note the use of the ``LLVM_CONFIG`` environment variable
   for specifying where your LLVM install is.

What to be aware of when using a system provided LLVM package.
..............................................................

When using a system provided LLVM package, there are a number of things that
could go wrong:

1. The LLVM package may not work with Numba/llvmlite at all.
2. If it does work to some degree it is unlikely the carry the correct patches
   for Numba/llvmlite to work entirely correctly.
3. Since the Numba/llvmlite maintainers may not know how the package was
   compiled it may be more difficult to get help when things do go wrong.

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

#. Download the `LLVM 10.0.1 source code <https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.1/llvm-10.0.1.src.tar.xz>`_.

#. Download or git checkout the `llvmlite source code <https://github.com/numba/llvmlite>`_.

#. Decompress the LLVM tar file and apply the following patches from the
   ``llvmlite/conda-recipes/`` directory.  You can apply each patch using the
   Linux ``patch -p1 -i {patch-file}`` command:

    #. ``llvm-lto-static.patch``: Fix issue with LTO shared library on Windows.
    #. ``partial-testing.patch``: Enables additional parts of the LLVM test
       suite.
    #. ``intel-D47188-svml-VF.patch``: Add support for vectorized math
       functions via Intel SVML.
    #. ``expect-fastmath-entrypoints-in-add-TLI-mappings.ll.patch``: Fix for a
       test failure caused by the previous patch.
    #. ``0001-Revert-Limit-size-of-non-GlobalValue-name.patch``: Revert the
       limit put on the length of a non-GlobalValue name.

#. For Linux/macOS:

    #. ``export PREFIX=desired_install_location CPU_COUNT=N``
       ( ``N`` is number of parallel compile tasks)
    #. Run the `build.sh <https://github.com/numba/llvmlite/blob/master/conda-recipes/llvmdev/build.sh>`_
       script in the llvmdev conda recipe from the LLVM source directory.

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
