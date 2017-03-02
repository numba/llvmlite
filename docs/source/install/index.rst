
Installing
==========

Pre-built binaries
------------------

For your own convenience, we recommend you install the pre-built binaries
provided for the Conda_ package manager.  Official binaries are available
in the Anaconda_ distribution; to install them, simply type::

   $ conda install llvmlite

If you want a more recent version, you can also fetch the automatic builds
available on Numba_'s `binstar channel <https://binstar.org/numba>`_::

   $ conda install --channel numba llvmlite

If don't want to use Conda, or modified llvmlite yourself, you will need
to build it.

Building manually
-----------------

Prerequisites (UNIX)
''''''''''''''''''''

You must have a LLVM 3.9 build (libraries and header files) available
somewhere.

Under a recent Ubuntu or Debian system, you may install the ``llvm-3.9-dev``
package if available.

If building LLVM on Ubuntu, the linker may report an error if the
development version of ``libedit`` is not installed. Install ``libedit-dev``
if you run into this problem.

Prerequisites (Windows)
'''''''''''''''''''''''

You must have Visual Studio 2013 or later (the free "Express" edition is ok)
in order to compile LLVM and llvmlite.  In addition, you must have cmake_
installed, and LLVM should have been built using cmake, in Release mode.
Be careful to use the right bitness (32- or 64-bit) for your Python
installation.

Compiling
'''''''''

Run ``python setup.py build``.  This builds the llvmlite C wrapper,
which embeds a statically-linked copy of the required subset of LLVM.

If your LLVM is installed in a non-standard location, first set the
``LLVM_CONFIG`` environment variable to the location of the corresponding
``llvm-config`` (or ``llvm-config.exe``) executable. For example if LLVM
is installed in ``/opt/llvm/`` with the ``llvm-config`` binary located at
``/opt/llvm/bin/llvm-config`` then set
``LLVM_CONFIG=/opt/llvm/bin/llvm-config``. This variable must be persisted
through into the installation of llvmlite e.g. into a python environment.

Installing
''''''''''

Validate your build by running the test suite: run ``python runtests.py``
or ``python -m llvmlite.tests``.  If everything works fine, install using
``python setup.py install``.


.. _cmake: http://www.cmake.org/
.. _Numba: http://numba.pydata.org/
.. _Conda: http://conda.pydata.org/
.. _Anaconda: http://docs.continuum.io/anaconda/index.html

