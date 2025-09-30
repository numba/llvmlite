.. _llvm20:

========================
LLVM 20 (llvmlite 0.45+)
========================

As of version 0.45 llvmlite supports LLVM 20. The build system has been updated
to use solely CMake, with added granularity about what is being consumed in
linkage, and additional build options. The llvmlite FFI binary exposes some of
these build options such that they can be queried at runtime. This was done
with a view of making sure that the new 100% public GHA based build system is
producing artifacts with the expected configurations and linkages. If you are
building packages or locally using a custom LLVM with llvmlite, the
installation documentation contains information about these options and how to
use the new CMake system.

.. _llvm20-build-system:

Specific changes due to LLVM 20/build system update
===================================================

#. All pointers emitted during code generation are now opaque, however,
   llvmlite APIs typically retain the types in the API and simply erase them
   during code generation.

#. The "LLVM legacy pass manager" has been removed along with associated APIs,
   the "LLVM new pass manager" APIs replace these. See the
   :ref:`legacy pass manager migration guide <passes-migration-guide>` for details
   on migrating from the legacy API to the new pass manager.

#. Initialization of LLVM core is now automatic. Calling :func:`llvmlite.binding.initialize`
   will now raise a ``RuntimeError`` with a message indicating that initialization
   is no longer required. See the API documentation for details.

#. The wheel builds and conda packages on the ``numba`` channel are built
   against an LLVM that has assertions enabled.

#. Moved to a single CMake based build system, static linking to LLVM is now
   default. This upgrade should make it easier for packagers of llvmlite, there
   is one build system with minimal variation across platforms and it uses the
   minimal required link libraries.

.. _llvm20-known-material-issues:

Known material issues with LLVM 20
==================================

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
