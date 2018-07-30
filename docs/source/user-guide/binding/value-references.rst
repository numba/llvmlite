================
Value references
================

.. currentmodule:: llvmlite.binding

A value reference is a wrapper around an LLVM value for you to 
inspect. You cannot create a value reference yourself. You get 
them from methods of the :class:`ModuleRef` class.

Enumerations
------------

.. class:: Linkage

   The linkage types allowed for global values are:

   * .. data:: external
   * .. data:: available_externally
   * .. data:: linkonce_any
   * .. data:: linkonce_odr
   * .. data:: linkonce_odr_autohide
   * .. data:: weak_any
   * .. data:: weak_odr
   * .. data:: appending
   * .. data:: internal
   * .. data:: private
   * .. data:: dllimport
   * .. data:: dllexport
   * .. data:: external_weak
   * .. data:: ghost
   * .. data:: common
   * .. data:: linker_private
   * .. data:: linker_private_weak


.. class:: Visibility

   The visibility styles allowed for global values are:

   * .. data:: default
   * .. data:: hidden
   * .. data:: protected


.. class:: StorageClass

   The storage classes allowed for global values are:

   * .. data:: default
   * .. data:: dllimport
   * .. data:: dllexport


The ValueRef class
------------------

.. class:: ValueRef

   A wrapper around an LLVM value. The attributes available are:

   * .. attribute:: is_declaration

        * ``True``---The global value is a mere declaration.
        * ``False``---The global value is defined in the given 
          module.

   * .. attribute:: linkage

        The linkage type---a :class:`Linkage` instance---for 
        this value. This attribute can be set.

   * .. attribute:: module

        The module---a :class:`ModuleRef` instance---that this 
        value is defined in.

   * .. attribute:: name

        This value's name, as a string. This attribute can be set.

   * .. attribute:: type

        This value's LLVM type as :class:`TypeRef` object.

   * .. attribute:: storage_class

        The storage 
        class---a :class:`StorageClass` instance---for 
        this value. This attribute can be set.

   * .. attribute:: visibility

        The visibility 
        style---a :class:`Visibility` instance---for 
        this value. This attribute can be set.
