
Types
=====

.. currentmodule:: llvmlite.ir

All values used in a LLVM module are explicitly typed.  Types all
derive from a common base class :class:`Type`.  Most of them can be
instantiated directly but some of them will need you to use other
APIs.  Once instantiated, a type should be considered immutable.

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


.. class:: FloatType()

   The type of single-precision floating-point real numbers.


.. class:: DoubleType()

   The type of double-precision floating-point real numbers.


.. class:: VoidType()

   The class for void types; only used as the return type of a
   function without a return value.


Aggregate types
---------------

.. class:: ArrayType(element, count)

   The class for arrays.  *element* is the type of every element, *count*
   the number of elements (a Python integer).


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

.. class:: MetaData

   The type for :term:`metadata`.  You don't need to instantiate this
   type.

