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

### Debian 7 ("[Wheezy](https://www.debian.org/releases/stable/)")

There are a few things that Debian users should keep in mind. First and foremost, the stable repositories will install LLVM 3.0, but we need version 3.5. Therefore, `apt-get install llvm-dev` will not work. You may want to compile it from source, or alternatively follow [these instructions](http://serverfault.com/a/382101/39594) and install `llvm-3.5-dev` from testing. After this, and particularly if there are multiple versions of `llvm` on your system, you may need to use `update-alternatives` to change the default version of the LLVM command-line tools — otherwise, the build script may not use LLVM 3.5.

It is also very important to note that `llvmlite` and `llvm` must be built with the same compiler. What this means if you install `llvm-3.5-dev` from testing is that `llvmlite` will have to be compiled with g++ 4.9. The steps to follow are the same as in the paragraph above: install `g++-4.9` from testing, then make it the default version with `update-alternatives` before running the build script.

See [issue #17](https://github.com/numba/llvmlite/issues/17) for an example of how the process might look like.

### Windows requirements

You must have Visual Studio 2012 or later (the free Express edition is ok). In addition, you must have [cmake](http://www.cmake.org/) installed, and LLVM should have been built using cmake, in Release mode. Be careful to use the right bitness (32- or 64-bit) for your Python installation.

## Run tests

Run `python runtests.py` or `python -m llvmlite.tests`.

## Install

Run `python setup.py install`.

