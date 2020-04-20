.. _faqs:

==========================
Frequently Asked Questions
==========================

.. _faq_supported_versions:

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


.. _faq_why_static:

Why Static Linking to LLVM?
===========================

The llvmlite package uses LLVM via ctypes calls to a C wrapper that is
statically linked to LLVM.  Some people are surprised that llvmlite uses
static linkage to LLVM, but there are several important reasons for this:

#. *The LLVM API has not historically been stable across releases* - Although
   things have improved since LLVM 4.0, there are still enough changes between
   LLVM releases to cause compilation issues if the right version is not
   matched with llvmlite.

#. *The LLVM shipped by most Linux distributions is not the version
   llvmlite needs* - The release cycles of Linux distributions will never line
   up with LLVM or llvmlite releases.

#. *We need to patch LLVM* - The binary packages of llvmlite are built
   against LLVM with a handful of patches to either fix bugs or to add
   features that have not yet been merged upstream.  In some cases, we've had
   to carry patches for several releases before they make it into LLVM.

#. *We don't need most of LLVM* - We are sensitive to the install size of
   llvmlite, and a full build of LLVM is quite large.  We can dramatically
   reduce the total disk needed by an llvmlite user (who typically doesn't
   need the rest of LLVM, ignoring the version matching issue) by statically
   linking to the library and pruning the symbols we do not need.

#. *Numba can use multiple LLVM builds at once* - Some Numba targets (AMD GPU,
   for example) may require different LLVM versions or non-mainline forks of
   LLVM to work.  These other LLVMs can be wrapped in a similar fashion as
   llvmlite, and will stay isolated.


Static linkage of LLVM was definitely not our goal early in Numba development,
but seems to have become the only workable solution given our constraints.
