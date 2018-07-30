=================
Type references
=================

.. currentmodule:: llvmlite.binding

A type reference wraps an LLVM type. It allows accessing type's name and 
IR representation. It is also accepted by methods like 
:meth:`TargetData.get_abi_size`.

The TypeRef class
------------------

.. class:: TypeRef

A wrapper around an LLVM type. The attributes available are:

* .. attribute:: name

    This type's name, as a string. 

* .. attribute:: is_pointer

    * ``True``---The type is a pointer type
    * ``False``---The type is not a pointer type

* .. attribute:: element_type

    If the type is a pointer, return the pointed-to type. Raises a
    ValueError if the type is not a pointer type.

* .. method:: __str__(self)

    Get the string IR representation of the type.
