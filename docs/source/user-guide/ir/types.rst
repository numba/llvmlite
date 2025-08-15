=====
Types
=====

.. currentmodule:: llvmlite.ir

.. contents::
   :local:
   :depth: 1


All :ref:`values <ir-values>` used in an LLVM module are
explicitly typed. All types derive from a common base class
:class:`Type`. You can instantiate most of them directly. Once
instantiated, a type should be considered immutable.

.. class:: Type

   The base class for all types.  Never instantiate it directly.
   Types have the following methods in common:

   * .. method:: as_pointer(addrspace=0)

        Return a :class:`PointerType` pointing to this type. The
        optional *addrspace* integer allows you to choose a
        non-default address space---the meaning is platform
        dependent.

   * .. method:: get_abi_size(target_data)

        Get the ABI size of this type, in bytes, according to the
        *target_data*---an :class:`llvmlite.binding.TargetData`
        instance.

   * .. method:: get_abi_alignment(target_data)

        Get the ABI alignment of this type, in bytes, according
        to the *target_data*---an
        :class:`llvmlite.binding.TargetData` instance.

   * .. method:: get_element_offset(target_data, position)

        Get the byte offset for the struct element at *position*,
        according to the *target_data*---an
        :class:`llvmlite.binding.TargetData` instance.

        NOTE: :meth:`get_abi_size`, :meth:`get_abi_alignment`,
        and :meth:`get_element_offset` call into the LLVM C++
        API to get the requested information.
        
   * .. method:: __call__(value)

        A convenience method to create a :class:`Constant` of
        this type with the given *value*::

           >>> int32 = ir.IntType(32)
           >>> c = int32(42)
           >>> c
           <ir.Constant type='i32' value=42>
           >>> print(c)
           i32 42


Atomic types
=============


.. class:: IntType(bits)

   The type of integers. The Python integer *bits* specifies the
   bitwidth of the integers having this type.

   .. attribute:: width

      The width in bits.

.. class:: HalfType()

   The type of half-precision, floating-point, real numbers.


.. class:: FloatType()

   The type of single-precision, floating-point, real numbers.


.. class:: DoubleType()

   The type of double-precision, floating-point, real numbers.


.. class:: VoidType()

   The class for void types. Used only as the return type of a
   function without a return value.


.. _pointer-types:

Pointer Types
=============

The IR layer presently supports both *Typed Pointers* and *Opaque Pointers*.
Support for Typed Pointers will eventually be removed.

.. note::
   Further details of the migration to Opaque Pointers are outlined in the
   section on :ref:`deprecation-of-typed-pointers`.

Typed Pointers are created using:

.. class:: PointerType(pointee, addrspace=0)

   The type of pointers to another type.

   Pointer types expose the following attributes:

   * .. attribute:: addrspace

        The pointer's address space number. This optional integer
        allows you to choose a non-default address space---the
        meaning is platform dependent.

   * .. attribute:: pointee

        The type pointed to.

Printing of Typed Pointers as Opaque Pointers can be enabled by setting the
environment variable:

.. code:: bash

   LLVMLITE_ENABLE_IR_LAYER_TYPED_POINTERS=0

or by setting the ``ir_layer_typed_pointers_enabled`` attribute after importing
llvmlite, but prior to using any of its functionality. For example:

.. code:: python

   import llvmlite
   llvmlite.ir_layer_typed_pointers_enabled = False

   # ... continue using llvmlite ...

Opaque Pointers can be created by using:

.. class:: PointerType(addrspace=0)
   :noindex:

   The type of pointers.

   Pointer types expose the following attribute:

   * .. attribute:: addrspace
        :noindex:

        The pointer's address space number. This optional integer
        allows you to choose a non-default address space---the
        meaning is platform dependent.


.. _aggregate-types:

Aggregate types
================

.. class:: Aggregate

   The base class for aggregate types. Never instantiate it
   directly. Aggregate types have the elements attribute in
   common.

   .. attribute:: elements

      A tuple-like immutable sequence of element types for this
      aggregate type.

.. class:: ArrayType(element, count)

   The class for array types.

   * *element* is the type of every element.
   * *count* is a Python integer representing the number of
     elements.

.. class:: VectorType(element, count)

   The class for vector types.

   * *element* is the type of every element.
   * *count* is a Python integer representing the number of
     elements.

.. class:: LiteralStructType(elements, [packed=False])

   The class for literal struct types.

   * *elements* is a sequence of element types for each member of the structure.
   * *packed* controls whether to use packed layout.

.. class:: IdentifiedStructType

   The class for identified struct types.  Identified structs are
   compared by name.  It can be used to make opaque types.

   Users should not create new instance directly.  Use the
   ``Context.get_identified_type`` method instead.

   An identified struct is created without a body (thus opaque).  To define the
   struct body, use the ``.set_body`` method.

   .. method:: set_body(*elems)

      Define the structure body with a sequence of element types.


Other types
============

.. class:: FunctionType(return_type, args, var_arg=False)

   The type of a function.

   * *return_type* is the return type of the function.
   * *args* is a sequence describing the types of argument to the
     function.
   * If *var_arg* is ``True``, the function takes a variable
     number of additional arguments of unknown types after the
     explicit args.

     EXAMPLE::

        int32 = ir.IntType(32)
        fnty = ir.FunctionType(int32, (ir.DoubleType(), ir.PointerType(int32)))

     An equivalent C declaration would be:

     .. code-block:: C

        typedef int32_t (*fnty)(double, int32_t *);


.. class:: LabelType

   The type for :ref:`labels <label>`.  You do not need to
   instantiate this type.

.. class:: MetaDataType

   The type for :ref:`metadata`. You do not need to
   instantiate this type.

   NOTE: This class was previously called "MetaData," but it was
   renamed for clarity.
