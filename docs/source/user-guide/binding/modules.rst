=======
Modules
=======

.. currentmodule:: llvmlite.binding

Although they conceptually represent the same thing, modules in
the :ref:`IR layer <ir-layer>` and modules in the
:ref:`binding layer <binding-layer>` do not have the same roles
and do not expose the same API.

While modules in the IR layer allow you to build and group
functions together, modules in the binding layer give access to
compilation, linking and execution of code. To distinguish
between them, the module class in the binding layer is
called :class:`ModuleRef` as opposed to
:class:`llvmlite.ir.Module`.

To go from the IR layer to the binding layer, use
the :func:`parse_assembly` function.

Factory functions
=================

You can create a module from the following factory functions:

* .. function:: parse_assembly(llvmir, context=None)

     Parse the given *llvmir*, a string containing some LLVM IR
     code. If parsing is successful, a new :class:`ModuleRef`
     instance is returned.

     * context: an instance of :class:`LLVMContextRef`.

        Defaults to the global context.

     EXAMPLE: You can obtain *llvmir* by calling ``str()`` on an
     :class:`llvmlite.ir.Module` object.

* .. function:: parse_bitcode(bitcode, context=None)

     Parse the given *bitcode*, a bytestring containing the
     LLVM bitcode of a module. If parsing is successful, a new
     :class:`ModuleRef` instance is returned.

     * context: an instance of :class:`LLVMContextRef`.

        Defaults to the global context.

     EXAMPLE: You can obtain the *bitcode* by calling
     :meth:`ModuleRef.as_bitcode`.


The ModuleRef class
===================

.. class:: ModuleRef

   A wrapper around an LLVM module object. The following methods
   and properties are available:

   * .. method:: as_bitcode()

        Return the bitcode of this module as a bytes object.

   * .. method:: get_function(name)

        Get the function with the given *name* in this module.

        If found, a :class:`ValueRef` is returned. Otherwise,
        :exc:`NameError` is raised.

   * .. method:: get_global_variable(name)

        Get the global variable with the given *name* in this
        module.

        If found, a :class:`ValueRef` is returned. Otherwise,
        :exc:`NameError` is raised.

    * .. method:: get_struct_type(name)

        Get the struct type with the given *name* in this module.

        If found, a :class:`TypeRef` is returned. Otherwise,
        :exc:`NameError` is raised.

   * .. method:: link_in(other, preserve=False)

        Link the *other* module into this module, resolving
        references wherever possible.

        * If *preserve* is ``True``, the other module is first
          copied in order to preserve its contents.
        * If *preserve* is ``False``, the other module is not
          usable after this call.

   * .. method:: verify()

        Verify the module's correctness. On error, raise
        :exc:`RuntimeError`.

   * .. attribute:: data_layout

        The data layout string for this module. This attribute
        can be set.

   * .. attribute:: functions

        An iterator over the functions defined in this module.
        Each function is a :class:`ValueRef` instance.

   * .. attribute:: global_variables

        An iterator over the global variables defined in this
        module. Each global variable is a :class:`ValueRef`
        instance.

   * .. attribute:: struct_types

        An iterator over the struct types defined in this module.
        Each type is a :class:`TypeRef` instance.

   * .. attribute:: name

        The module's identifier, as a string. This attribute can
        be set.

   * .. attribute:: source_file

        The module's reported source file, as a string. This
        attribute can not be set.
	
   * .. attribute:: triple

        The platform "triple" string for this module. This
        attribute can be set.
