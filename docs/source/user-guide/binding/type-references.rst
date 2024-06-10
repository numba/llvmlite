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

    * .. attribute:: is_struct

        * ``True``---The type is a struct type
        * ``False``---The type is not a struct type

    * .. attribute:: is_pointer

        * ``True``---The type is a pointer type
        * ``False``---The type is not a pointer type

    * .. attribute:: is_array

        * ``True``---The type is an array type
        * ``False``---The type is not an array type

    * .. attribute:: is_vector

        * ``True``---The type is a vector type
        * ``False``---The type is not a vector type

    * .. attribute:: is_function_vararg

        * ``True``--- The function type accepts a variable number of arguments
        * ``False``---The function type accepts a fixed number of arguments

    * .. attribute:: elements

        Returns an iterator over enclosing types. For example,
        the elements of an array or members of a struct.

    * .. attribute:: element_type

        If the type is a pointer, return the pointed-to type. Raises a
        ValueError if the type is not a pointer type.

    * .. attribute:: element_count

        Returns the number of elements in an array or a vector. For scalable
        vectors, returns minimum number of elements. When the type is neither
        an array nor a vector, raises exception.

    * .. attribute:: type_width

        Return the basic size of this type if it is a primitive type. These are
        fixed by LLVM and are not target-dependent.
        This will return zero if the type does not have a size or is not a
        primitive type.

        If this is a scalable vector type, the scalable property will be set and
        the runtime size will be a positive integer multiple of the base size.

        Note that this may not reflect the size of memory allocated for an
        instance of the type or the number of bytes that are written when an
        instance of the type is stored to memory.

    * .. attribute:: type_kind

        Returns the ``LLVMTypeKind`` enumeration of this type.

    * .. method:: as_ir(self, ir_ctx)

        Convert into an ``llvmlite.ir.Type``.

    * .. method:: __str__(self)

        Get the string IR representation of the type.
