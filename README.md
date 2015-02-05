# llvmlite

A lightweight LLVM python binding for writing JIT compilers

Old [llvmpy](https://github.com/llvmpy/llvmpy) binding exposes a lot of LLVM but the mapping of C++ style memory management to python is error prone. Numba and many JIT compiler does not need a full LLVM API. Only the IR builder, optimizer, and JIT compiler APIs are necessary.

llvmlite is a project originally tailored for Numba's needs, using the following approach:

- A small C wrapper around the parts of the LLVM C++ API we need that are
not already exposed by the LLVM C API.
- A ctypes Python wrapper around the C API.
- A pure Python implementation of the subset of the LLVM IR builder that we
need for Numba.

## Key Benefits

- llvmlite IR builder is pure python
- llvmlite uses LLVM assembly parser which provide better error messages (no more segfault due to bad IR construction)
- Most of llvmlite uses the LLVM C API which is small but very stable and backward compatible (low maintenance when changing LLVM version)
- The binding is not a python C-extension (no need to wrestle with Python's compiler requirement and C++11 compatibility)
- llvmlite binding memory management is explicit obj.close() or with-context
- llvmlite is quite faster in early benchmarks (the Numba test suite is twice faster)

## LLVMPY Compatibility Layer

`llvmlite.llvmpy.*` provides a minimal LLVMPY compatibility layer.

## Dependencies

You need Python 2.6 or greater (including Python 3.3 or greater).

### Build dependencies

- LLVM 3.5
- A C compiler, and possibly other tools (see below)

### Runtime dependencies

- For Python versions before 3.4, the [enum34](https://pypi.python.org/pypi/enum34) package is required

## Build

Run `python setup.py build`. This will build the llvmlite C wrapper, which will contain a statically-linked copy of the required subset of LLVM.

If your LLVM is installed in a non-standard location, first point the `LLVM_CONFIG` environment variable to the path of the corresponding `llvm-config` executable.

### Unix requirements

You must have a LLVM 3.5 build (libraries and header files) available somewhere. If it is not installed in a standard location, you may have to tweak the build script. Under Ubuntu 14.10 and Debian unstable, you can install `llvm-3.5-dev`. Versions shipped with earlier versions (Ubuntu 14.04, Debian stable) may not be good enough.

When building on Ubuntu, the linker may report an error if the development version of ``libedit`` is not installed. Install ``libedit-dev`` if you run into this problem.

### Windows requirements

You must have Visual Studio 2012 or later (the free Express edition is ok). In addition, you must have [cmake](http://www.cmake.org/) installed, and LLVM should have been built using cmake, in Release mode. Be careful to use the right bitness (32- or 64-bit) for your Python installation.

## Run tests

Run `python runtests.py` or `python -m llvmlite.tests`.

## Install

Run `python setup.py install`.

