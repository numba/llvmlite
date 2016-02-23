
Modules
=======

.. currentmodule:: llvmlite.binding


While they conceptually represent the same thing, modules in the
:ref:`IR layer <ir-layer>` and modules in the :ref:`binding layer
<binding-layer>` don't have the same roles and don't expose the same API.

While modules in the IR layer allow to build and group functions together,
modules in the binding layer give access to compilation, linking and
execution of code.  To distinguish between the two, the module class
in the binding layer is called :class:`ModuleRef` as opposed to
:class:`llvmlite.ir.Module`.

To go from one realm to the other, you must use the :func:`parse_assembly`
function.

Factory functions
-----------------

A module can be created from the following factory functions:

.. function:: parse_assembly(llvmir)

   Parse the given *llvmir*, a string containing some LLVM IR code.  If
   parsing is successful, a new :class:`ModuleRef` instance is returned.

   *llvmir* can be obtained, for example, by calling ``str()`` on a
   :class:`llvmlite.ir.Module` object.

.. function:: parse_bitcode(bitcode)

   Parse the given *bitcode*, a bytestring containing the LLVM bitcode
   of a module.  If parsing is successful, a new :class:`ModuleRef`
   instance is returned.

   *bitcode* can be obtained, for example, by calling
   :meth:`ModuleRef.as_bitcode`.


The ModuleRef class
-------------------

.. class:: ModuleRef

   A wrapper around a LLVM module object.  The following methods and
   properties are available:

   .. method:: as_bitcode()

      Return the bitcode of this module as a bytes object.

   .. method:: get_function(name)

      Get the function with the given *name* in this module.  If found,
      a :class:`ValueRef` is returned.  Otherwise, :exc:`NameError`
      is raised.

   .. method:: get_global_variable(name)

      Get the global variable with the given *name* in this module.
      If found, a :class:`ValueRef` is returned.  Otherwise, :exc:`NameError`
      is raised.

   .. method:: link_in(other, preserve=False)

      Link the *other* module into this module, resolving references
      wherever possible.  If *preserve* is true, the other module is first
      copied in order to preserve its contents; if *preserve* is false,
      the other module is not usable after this call anymore.

   .. method:: verify()

      Verify the module's correctness.  :exc:`RuntimeError` is raised on
      error.

   .. attribute:: data_layout

      The data layout string for this module.  This attribute is settable.

   .. attribute:: functions

      An iterator over the functions defined in this module.
      Each function is a :class:`ValueRef` instance.

   .. attribute:: global_variables

      An iterator over the global variables defined in this module.
      Each global variable is a :class:`ValueRef` instance.

   .. attribute:: name

      The module's identifier, as a string.  This attribute is settable.

   .. attribute:: triple

      The platform "triple" string for this module.  This attribute is settable.

