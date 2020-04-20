.. _faqs:

==========================
Frequently Asked Questions
==========================

Why doesn't ``llvmlite`` always support the latest release(s) of LLVM?
======================================================================

There's a few reasons for this:

1. Most importantly, if llvmlite declares it supports a given version of LLVM,
   it means that the development team has verified that the particular LLVM
   version will work for llvmlite uses, mainly that it works fine for JIT
   compiler projects (like Numba). This testing is extensive and it's not
   uncommon to have to patch LLVM in the process/make decisions about the
   severity of problems/report problems upstream to LLVM. Ultimately, if the
   build is not considered stable across all supported architectures/OS
   combinations then support is not declared.

2. LLVM sometimes updates its API or internal behaviour and it takes time
   to work out what needs to be done to accommodate this on all of llvmlite's
   supported architectures/OS combinations.

3. There is a set of patches that ship along with the LLVM builds for llvmlite.
   These patches are necessary and often need porting to work on new LLVM
   versions, this takes time and requires testing. It should be noted that LLVM
   builds that come with e.g. linux distributions may not work well with the
   llvmlite intended use cases.
