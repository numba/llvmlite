.. _llvm22:

========================
LLVM 22 (llvmlite 0.48+)
========================

As of version 0.48 llvmlite supports LLVM 22. This release upgrades the LLVM
toolchain from LLVM 20 (llvmlite 0.45--0.47). The CMake-based build system,
static linking defaults, and packaging layout introduced in :ref:`llvm20` are
unchanged.

If you are upgrading from llvmlite 0.47 or earlier on LLVM 20, read
:ref:`llvm20` for background on the 0.45 migration, then review the notes
below for LLVM 22.

Size optimization flags removed
===============================

LLVM 22 removes the ``Os`` and ``Oz`` size optimization levels from
``OptimizationLevel``. Size optimization is now expressed through the
per-function ``optsize`` and ``minsize`` attributes instead. See
:ref:`optimizing-for-size` for how to request size optimization in llvmlite.

.. _llvm22-known-material-issues:

Known material issues with LLVM 22
==================================

The following issues were known with LLVM 20 and may still apply on LLVM 22;
please report regressions or fixes on the issue tracker.

#. Intel SVML is currently unsupported. The patch from LLVM 15 did not apply
   cleanly and fixing it was non-trivial. It is hoped that this can be
   resolved in the future.

#. There is an issue with calling global constructors/destructors from MCJIT on
   OSX platforms the result of which is that calling an execution engine’s
   ``run_static_constructors`` method will result in an assertion error or a
   segmentation fault depending on whether LLVM has assertions enabled. The
   cause of this is that the use of ``__mod_term_func`` has been deprecated, which
   means that LLVM now emits a ``__cxa_atexit`` call in the constructor to
   schedule the execution of destructors, see
   https://github.com/llvm/llvm-project/commit/22570bac694396514fff18dec926558951643fa6.
   MCJIT does not correctly support ``__cxa_atexit`` and so hits an assertion
   error or segmentation faults when the static constructors are called (the
   linker should handle it so that it can be called with a live JIT library,
   but this does not happen, and so the ``atexit`` handlers for the process run
   it instead, by which time the JIT library has been destroyed, the result of
   which is typically a segmentation fault due to ``__cxa_atexit`` accessing an
   invalid address). Multiple workarounds were tried by “faking” various
   missing parts, but the effect was a lot of complexity that seemingly
   pushes the problem to some other area. It needs fixing at the LLVM level.

#. The toolchain version used to compile LLVM and llvmlite needs to be the same
   in both builds. When using the Anaconda/conda-forge distribution toolchains,
   the result of using inconsistent versions is typically a segmentation fault.
   It is suspected that this issue arises due to minor ABI differences but
   investigation has not gone further than figuring out that the version
   difference across the packages was the cause of the problem. An example of
   correctly using versions would be: if LLVM is compiled with GCC 11 tooling,
   then llvmlite should also be compiled with GCC 11 tooling.

#. The ``.text`` sections in ORC JIT compiled ELF objects are now called
   ``.ltext`` (other sections have a similar ``l`` prefix)

#. The ORC JIT compilation chain now defaults to letting the JIT process access
   the symbols present in the “main” process.
