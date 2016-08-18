
Types
=====

.. currentmodule:: llvmlite.ir

All :ref:`values <ir-values>` used in a LLVM module are explicitly typed.
All types derive from a common base class :class:`Type`.  Most of them can be
instantiated directly.  Once instantiated, a type should be considered
immutable.

.. class:: Type

   The base class for all types.  You should never instantiate it directly.
   Types have the following methods in common:

   .. method:: as_pointer(addrspace=0)

      Return a :class:`PointerType` pointing to this type.  The optional
      *addrspace* integer allows you to choose a non-default address
      space (the meaning is platform-dependent).

   .. method:: get_abi_size(target_data)

      Get the ABI size of this type, in bytes, according to the *target_data*
      (a :class:`llvmlite.binding.TargetData` instance).

   .. method:: get_abi_alignment(target_data)

      Get the ABI alignment of this type, in bytes, according to the
      *target_data* (a :class:`llvmlite.binding.TargetData` instance).

      .. note::
         :meth:`get_abi_size` and :meth:`get_abi_alignment` call into the
         LLVM C++ API to get the requested information.

   .. method:: __call__(value)

      Convenience method to create a :class:`Constant` of this type with
      the given *value*::

         >>> int32 = ir.IntType(32)
         >>> c = int32(42)
         >>> c
         <ir.Constant type='i32' value=42>
         >>> print(c)
         i32 42


Atomic types
------------

.. class:: PointerType(pointee, addrspace=0)

   The type of pointers to another type.  *pointee* is the type pointed to.
   The optional *addrspace* integer allows you to choose a non-default
   address space (the meaning is platform-dependent).

   Pointer types exposes the following attributes:

   .. attribute:: addrspace

      The pointer's address space number.

   .. attribute:: pointee

      The type pointed to.


.. class:: IntType(bits)

   The type of integers.  *bits*, a Python integer, specifies the bitwidth
   of the integers having this type.

   .. attribute:: width

      The width in bits.


.. class:: FloatType()

   The type of single-precision floating-point real numbers.


.. class:: DoubleType()

   The type of double-precision floating-point real numbers.


.. class:: VoidType()

   The class for void types; only used as the return type of a
   function without a return value.


.. _aggregate-types:

Aggregate types
---------------

.. class:: Aggregate

   The base class for aggregate types.  You should never instantiate it
   directly.  Aggregate types have the following attribute in common:

   .. attribute:: elements

      A tuple-like immutable sequence of element types for this aggregate
      type.


.. class:: ArrayType(element, count)

   The class for array types.  *element* is the type of every element, *count*
   the number of elements (a Python integer).

.. class:: LiteralStructType(elements)

   The class for literal struct types.  *elements* is a sequence of element
   types for each member of the structure.

.. .. class:: IdentifiedStructType

   I prefer not documenting this before the straighten out the API, which
   is currently weird.


Other types
-----------

.. class:: FunctionType(return_type, args, var_arg=False)

   The type of a function.  *return_type* is the return type of the
   function.  *args* is a sequence describing the types of argument
   to the function.  If *var_arg* is true, the function takes a variable
   number of additional arguments (of unknown types) after the
   explicit *args*.

   Example::

      int32 = ir.IntType(32)
      fnty = ir.FunctionType(int32, (ir.DoubleType(), ir.PointerType(int32)))

   An equivalent C declaration would be:

   .. code-block:: C

      typedef int32_t (*fnty)(double, int32_t *);


.. class:: LabelType

   The type for :term:`labels <label>`.  You don't need to instantiate this
   type.

.. class:: MetaDataType

   The type for :term:`metadata`.  You don't need to instantiate this
   type.

   .. note::
      This used to be called ``MetaData`` but was renamed for clarity.
