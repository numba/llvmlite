===============================
Initialization and finalization
===============================

.. currentmodule:: llvmlite.binding

You only need to call these functions once per process invocation.

* .. function:: initialize()

     Initialize the LLVM core.

     **Deprecated.** Initialize the LLVM core.

     This function is deprecated and will raise a RuntimeError when
     called. LLVM initialization is now handled automatically and no longer
     requires explicit initialization calls. Remove calls to this function and
     check for other behavioral changes that may have occurred due to LLVM
     updates.

* .. function:: initialize_all_targets()

     Initialize all targets. Must be called before targets can
     be looked up via the :class:`Target` class.

* .. function:: initialize_all_asmprinters()

     Initialize all code generators. Must be called before
     generating any assembly or machine code via the
     :meth:`TargetMachine.emit_object` and
     :meth:`TargetMachine.emit_assembly` methods.

* .. function:: initialize_native_target()

     Initialize the native---host---target. Must be called once
     before doing any code generation.


* .. function:: initialize_native_asmprinter()

     Initialize the native assembly printer.


* .. function:: initialize_native_asmparser()

     Initialize the native assembly parser. Must be called for
     inline assembly to work.

* .. function:: shutdown()

     Shut down the LLVM core.


* .. data:: llvm_version_info

     A 3-integer tuple representing the LLVM version number.

     EXAMPLE: ``(3, 7, 1)``

     Since LLVM is statically linked into the ``llvmlite`` DLL,
     this is guaranteed to represent the true LLVM version in use.
     
