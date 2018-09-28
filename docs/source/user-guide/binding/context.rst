Context
============

LLVMContext is an opaque context reference used to group modules into logical groups.
For example, the type names are unique within a context, the name collisions
are resolved by LLVM automatically.

LLVMContextRef
--------------

A wrapper around LLVMContext. Should not be instantiated directly, use the
following methods:

.. class:: LLVMContextRef

* .. function:: create_context():

    Create a new LLVMContext instance.

* .. function:: get_global_context():

    Get the reference to the global context.