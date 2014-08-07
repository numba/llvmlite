# llvmlite

A lightweight LLVM python binding for writing JIT compilers

Old llvmpy (https://github.com/llvmpy/llvmpy) binding exposes a lot of LLVM but the mapping of C++ style memory management to python is error prone. Numba and many JIT compiler does not need a full LLVM API. Only the IR builder, optimizer, and JIT compiler APIs are necessary.

## Key Benefits

- llvmlite IR builder is pure python
- llvmlite uses LLVM assembly parser which provide better error messages (no more segfault due to bad IR construction)
- Most of llvmlite uses the LLVM C API which is small but very stable and backward compatible (low maintenance when changing LLVM version)
- The binding in llvmlite is optional (only if you are using ``llvmlite.binding``)
- The binding is not a python C-extension (no need to wrestle with Python's compiler requirement and C++11 compatibility)
- llvmlite binding memory management is explicit obj.close() or with-context
- llvmlite is 1.5x faster in early benchmark (compiling numba.tests.usecases.andor)


## LLVMPY Compatibility Layer

`llvmlite.llvmpy.*` provides a minimal LLVMPY compatibility layer.

## Build

### LLVM binding

The LLVM binding is optional.  It is only necessary if ``llvmlite.binding`` is used.  Note: ``llvmlite.llvmpy.*`` depends on ``llvmlite.binding``.

Steps:
 - Run `make` in "<srcroot>/ffi" 


### Install Python extension

TODO

