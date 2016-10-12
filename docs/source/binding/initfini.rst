
Initialization and finalization
===============================

.. currentmodule:: llvmlite.binding

These functions need only be called once per process invocation.


.. function:: initialize()

   Initialize the LLVM core.

.. function:: initialize_all_targets()

   Initialize all targets. Necessary before targets can be looked up
   via the :class:`Target` class.

.. function:: initialize_all_asmprinters()

   Initialize all code generators. Necessary before generating
   any assembly or machine code via the :meth:`TargetMachine.emit_object`
   and :meth:`TargetMachine.emit_assembly` methods.

.. function:: initialize_native_target()

   Initialize the native (host) target.  Calling this function once is
   necessary before doing any code generation.


.. function:: initialize_native_asmprinter()

   Initialize the native assembly printer.


.. function:: initialize_native_asmparser()

   Initialize the native assembly parser.  This is necessary for inline assembly
   to work.

.. function:: shutdown()

   Shutdown the LLVM core.


.. data:: llvm_version_info

   A three-integer tuple representing the LLVM version number,
   for example ``(3, 7, 1)``.  Since LLVM is statically linked into
   the ``llvmlite`` DLL, this is guaranteed to represent the true LLVM
   version in use.
