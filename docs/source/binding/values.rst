
Value references
================

.. currentmodule:: llvmlite.binding


A value reference is a wrapper around a LLVM value for you to inspect.
You can't create one yourself; instead, you'll get them from methods
of the :class:`ModuleRef` class.


Enumerations
------------

.. class:: Linkage

   The different linkage types allowed for global values.  The following
   values are provided:

   .. data:: external
   .. data:: available_externally
   .. data:: linkonce_any
   .. data:: linkonce_odr
   .. data:: linkonce_odr_autohide
   .. data:: weak_any
   .. data:: weak_odr
   .. data:: appending
   .. data:: internal
   .. data:: private
   .. data:: dllimport
   .. data:: dllexport
   .. data:: external_weak
   .. data:: ghost
   .. data:: common
   .. data:: linker_private
   .. data:: linker_private_weak

The ValueRef class
------------------

.. class:: ValueRef

   A wrapper around a LLVM value.  The following properties are available:

   .. attribute:: is_declaration

      True if the global value is a mere declaration, False if it is
      defined in the given module.

   .. attribute:: linkage

      The linkage type (a :class:`Linkage` instance) for this value.  This
      attribute is settable.

   .. attribute:: module

      The module (a :class:`ModuleRef` instance) this value is defined in.

   .. attribute:: name

      This value's name, as a string.  This attribute is settable.

   .. attribute:: type

      This value's LLVM type.  An opaque object is returned.  It can be used
      with e.g. :meth:`TargetData.get_abi_size`.

   .. method:: view_cfg

      Generate a DOT file of the CFG of a function with instructions.


   .. method:: view_cfg_only

      Generate a DOT file of the CFG of a function without instructions.
