
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

You must have a LLVM 3.5 build (libraries and header files) available
somewhere.

Under Ubuntu 14.10 and Debian, you can install the ``llvm-3.5-dev``
package.  LLVM packages shipped with some earlier distributions such as
Ubuntu 14.04 are known to be broken.

If building on Ubuntu, the linker may report an error if the development
version of ``libedit`` is not installed. Install ``libedit-dev`` if you
run into this problem.

Prerequisites (Windows)
'''''''''''''''''''''''

You must have Visual Studio 2012 or later (the free "Express" edition is ok)
in order to compile LLVM and llvmlite.  In addition, you must have cmake_
installed, and LLVM should have been built using cmake, in Release mode.
Be careful to use the right bitness (32- or 64-bit) for your Python
installation.

Compiling
'''''''''

Run ``python setup.py build``.  This builds the llvmlite C wrapper,
which embeds a statically-linked copy of the required subset of LLVM.

If your LLVM is installed in a non-standard location, first point the
``LLVM_CONFIG`` environment variable to the path of the corresponding
``llvm-config`` (or ``llvm-config.exe``) executable.

Installing
''''''''''

Validate your build by running the test suite: run ``python runtests.py``
or ``python -m llvmlite.tests``.  If everything works fine, install using
``python setup.py install``.


.. _cmake: http://www.cmake.org/
.. _Numba: http://numba.pydata.org/
.. _Conda: http://conda.pydata.org/
.. _Anaconda: http://docs.continuum.io/anaconda/index.html

