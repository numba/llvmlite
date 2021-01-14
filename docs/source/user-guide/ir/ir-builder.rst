===========
IR builders
===========

.. currentmodule:: llvmlite.ir

.. contents::
   :depth: 2
   :local:


:class:`IRBuilder` is the workhorse of LLVM :ref:`IR` generation.
It allows you to fill the :ref:`basic blocks <basic block>` of
your functions with LLVM instructions.

An :class:`IRBuilder` internally maintains a current basic block
and a pointer inside the block's list of instructions. When a
new instruction is added, it is inserted at that point, and then
the pointer is advanced after the new instruction.

A :class:`IRBuilder` also maintains a reference to metadata
describing the current source location, which is attached to all
inserted instructions.


Instantiation
==============

.. class:: IRBuilder(block=None)

   Create a new IR builder. If *block*---a :class:`Block`---is
   given, the builder starts at the end of this basic block.


Attributes
==========

:class:`IRBuilder` has the following attributes:

*  .. attribute:: IRBuilder.block

      The basic block that the builder is operating on.

*  .. attribute:: IRBuilder.function

      The function that the builder is operating on.

*  .. attribute:: IRBuilder.module

      The module that the builder's function is defined in.

*  .. attribute:: IRBuilder.debug_metadata

      If not ``None``, the metadata that is attached to any
      inserted instructions as ``!dbg``, unless the instruction
      already has ``!dbg`` set.


Utilities
=========

.. method:: IRBuilder.append_basic_block(name='')

   Append a basic block, with the given optional *name*, to the
   current function. The current block is not changed. A
   :class:`Block` is returned.


Positioning
===========

The following :class:`IRBuilder` methods help you move the
current instruction pointer:

* .. method:: IRBuilder.position_before(instruction)

     Position immediately before the given *instruction*. The
     current block is also changed to the instruction's basic
     block.

* .. method:: IRBuilder.position_after(instruction)

     Position immediately after the given *instruction*. The
     current block is also changed to the instruction's basic
     block.

* .. method:: IRBuilder.position_at_start(block)

     Position at the start of the basic *block*.

* .. method:: IRBuilder.position_at_end(block)

     Position at the end of the basic *block*.

The following context managers allow you to temporarily switch to
another basic block and then go back to where you were.

* .. method:: IRBuilder.goto_block(block)

     Position the builder either at the end of the
     basic *block*, if it is not terminated, or just before the
     *block*'s terminator::

        new_block = builder.append_basic_block('foo')
        with builder.goto_block(new_block):
           # Now the builder is at the end of *new_block*
           # ... add instructions

        # Now the builder has returned to its previous position

* .. method:: IRBuilder.goto_entry_block()

     The same as :meth:`goto_block`, but with the current
     function's entry block.


Flow control helpers
=====================

The following context managers make it easier to create
conditional code.

* .. method:: IRBuilder.if_then(pred, likely=None)

     Create a basic block whose execution is conditioned on
     predicate *pred*, a value of type ``IntType(1)``. Another
     basic block is created for instructions after the
     conditional block. The current basic block is terminated
     with a conditional branch based on *pred*.

     When the context manager is entered, the builder positions
     at the end of the conditional block. When the context
     manager is exited, the builder positions at the start of
     the continuation block.

     If likely is not ``None``, it indicates whether *pred* is
     likely to be ``True``, and metadata is emitted to specify
     branch weights accordingly.


* .. method:: IRBuilder.if_else(pred, likely=None)

     Set up 2 basic blocks whose execution is conditioned on
     predicate *pred*, a value of type ``IntType(1)``. *likely* has
     the same meaning as in ``if_then()``.

     A pair of context managers is yielded. Each of them acts as
     an :meth:`if_then()` context manager---the first for the
     block to be executed if pred is ``True`` and the second for
     the block to be executed if pred is ``False``.

     When the context manager is exited, the builder is
     positioned on a new continuation block that both
     conditional blocks jump into.

     Typical use:

     .. code-block:: Python

        with builder.if_else(pred) as (then, otherwise):
            with then:
                # emit instructions for when the predicate is true
            with otherwise:
                # emit instructions for when the predicate is false
        # emit instructions following the if-else block


Instruction building
=====================

The following methods insert a new instruction---an
:class:`Instruction` instance---at the current index in the
current block. The new instruction is returned.

An instruction's operands are almost always
:ref:`values <ir-values>`.

Many of these methods also take an optional *name* argument,
specifying the local *name* of the result value. If not given, a
unique name is automatically generated.


Arithmetic
------------

In the methods below, the *flags* argument is an optional sequence
of strings that modify the instruction's semantics. Examples
include the fast-math flags for floating-point operations, and
whether wraparound on overflow can be ignored on integer
operations.


Integer
^^^^^^^

* .. method:: IRBuilder.shl(lhs, rhs, name='', flags=())

     Left-shift *lhs* by *rhs* bits.

* .. method:: IRBuilder.lshr(lhs, rhs, name='', flags=())

     Logical right-shift *lhs* by *rhs* bits.

* .. method:: IRBuilder.ashr(lhs, rhs, name='', flags=())

     Arithmetic, signed, right-shift *lhs* by *rhs* bits.

* .. method:: IRBuilder.cttz(value, flag)

     Counts trailing zero bits in *value*. Boolean *flag* indicates whether the
     result is defined for ``0``.

* .. method:: IRBuilder.ctlz(value, flag)

     Counts leading zero bits in *value*. Boolean *flag* indicates whether the
     result is defined for ``0``.

* .. method:: IRBuilder.add(lhs, rhs, name='', flags=())

     Integer add *lhs* and *rhs*.

* .. method:: IRBuilder.sadd_with_overflow(lhs, rhs, name='', flags=())

     Integer add *lhs* and *rhs*. A ``{ result, overflow bit }``
     structure is returned.

* .. method:: IRBuilder.sub(lhs, rhs, name='', flags=())

     Integer subtract *rhs* from *lhs*.

* .. method:: IRBuilder.ssub_with_overflow(lhs, rhs, name='', flags=())

     Integer subtract *rhs* from *lhs*. A
     ``{ result, overflow bit }`` structure is returned.

* .. method:: IRBuilder.mul(lhs, rhs, name='', flags=())

     Integer multiply *lhs* with *rhs*.

* .. method:: IRBuilder.smul_with_overflow(lhs, rhs, name='', flags=())

     Integer multiply *lhs* with *rhs*. A
     ``{ result, overflow bit }`` structure is returned.

* .. method:: IRBuilder.sdiv(lhs, rhs, name='', flags=())

     Signed integer divide *lhs* by *rhs*.

* .. method:: IRBuilder.udiv(lhs, rhs, name='', flags=())

     Unsigned integer divide *lhs* by *rhs*.

* .. method:: IRBuilder.srem(lhs, rhs, name='', flags=())

     Signed integer remainder of *lhs* divided by *rhs*.

* .. method:: IRBuilder.urem(lhs, rhs, name='', flags=())

     Unsigned integer remainder of *lhs* divided by *rhs*.

* .. method:: IRBuilder.and_(lhs, rhs, name='', flags=())

     Bitwise AND *lhs* with *rhs*.

* .. method:: IRBuilder.or_(lhs, rhs, name='', flags=())

     Bitwise OR *lhs* with *rhs*.

* .. method:: IRBuilder.xor(lhs, rhs, name='', flags=())

     Bitwise XOR *lhs* with *rhs*.

* .. method:: IRBuilder.not_(value, name='')

     Bitwise complement *value*.

* .. method:: IRBuilder.neg(value, name='')

     Negate *value*.

Floating-point
^^^^^^^^^^^^^^

* .. method:: IRBuilder.fadd(lhs, rhs, name='', flags=())

     Floating-point add *lhs* and *rhs*.

* .. method:: IRBuilder.fsub(lhs, rhs, name='', flags=())

     Floating-point subtract *rhs* from *lhs*.

* .. method:: IRBuilder.fmul(lhs, rhs, name='', flags=())

     Floating-point multiply *lhs* by *rhs*.

* .. method:: IRBuilder.fdiv(lhs, rhs, name='', flags=())

     Floating-point divide *lhs* by *rhs*.

* .. method:: IRBuilder.frem(lhs, rhs, name='', flags=())

     Floating-point remainder of *lhs* divided by *rhs*.

* .. method:: IRBuilder.fneg(arg, name='', flags=())

     Floating-point negation of *arg*.


Conversions
-----------

* .. method:: IRBuilder.trunc(value, typ, name='')

     Truncate integer *value* to integer type *typ*.

* .. method:: IRBuilder.zext(value, typ, name='')

     Zero-extend integer *value* to integer type *typ*.

* .. method:: IRBuilder.sext(value, typ, name='')

     Sign-extend integer *value* to integer type *typ*.

* .. method:: IRBuilder.fptrunc(value, typ, name='')

     Truncate---approximate---floating-point *value* to
     floating-point type *typ*.

* .. method:: IRBuilder.fpext(value, typ, name='')

     Extend floating-point *value* to floating-point type *typ*.

* .. method:: IRBuilder.fptosi(value, typ, name='')

     Convert floating-point *value* to signed integer type *typ*.

* .. method:: IRBuilder.fptoui(value, typ, name='')

     Convert floating-point *value* to unsigned integer type *typ*.

* .. method:: IRBuilder.sitofp(value, typ, name='')

     Convert signed integer *value* to floating-point type *typ*.

* .. method:: IRBuilder.uitofp(value, typ, name='')

     Convert unsigned integer *value* to floating-point type *typ*.

* .. method:: IRBuilder.ptrtoint(value, typ, name='')

     Convert pointer *value* to integer type *typ*.

* .. method:: IRBuilder.inttoptr(value, typ, name='')

     Convert integer *value* to pointer type *typ*.

* .. method:: IRBuilder.bitcast(value, typ, name='')

     Convert pointer *value* to pointer type *typ*.

* .. method:: IRBuilder.addrspacecast(value, typ, name='')

     Convert pointer *value* to pointer type *typ* of different
     address space.


Comparisons
------------

* .. method:: IRBuilder.icmp_signed(cmpop, lhs, rhs, name='')

     Signed integer compare *lhs* with *rhs*. The string *cmpop* can
     be one of ``<``, ``<=``, ``==``, ``!=``, ``>=`` or ``>``.

* .. method:: IRBuilder.icmp_unsigned(cmpop, lhs, rhs, name='')

     Unsigned integer compare *lhs* with *rhs*. The string *cmpop* can
     be one of ``<``, ``<=``, ``==``, ``!=``, ``>=`` or ``>``.

* .. method:: IRBuilder.fcmp_ordered(cmpop, lhs, rhs, name='', flags=[])

     Floating-point ordered compare *lhs* with *rhs*.

     * The string *cmpop* can be one of ``<``, ``<=``, ``==``,
       ``!=``, ``>=``, ``>``, ``ord`` or ``uno``.
     * The *flags* list can include any of ``nnan``, ``ninf``,
       ``nsz``, ``arcp`` and ``fast``, which implies all
       previous flags.

* .. method:: IRBuilder.fcmp_unordered(cmpop, lhs, rhs, name='', flags=[])

     Floating-point unordered compare *lhs* with *rhs*.

     * The string *cmpop*, can  be one of ``<``, ``<=``, ``==``,
       ``!=``, ``>=``, ``>``, ``ord`` or ``uno``.
     * The *flags* list can include any of ``nnan``, ``ninf``,
       ``nsz``, ``arcp`` and ``fast``, which implies all
       previous flags.


Conditional move
-----------------

.. method:: IRBuilder.select(cond, lhs, rhs, name='')

   A 2-way select---*lhs* if *cond*, else *rhs*.


Phi
---

.. method:: IRBuilder.phi(typ, name='')

   Create a phi node. To add incoming edges and their values, use
   the :meth:`~PhiInstr.add_incoming` method on the return value.


Aggregate operations
---------------------

* .. method:: IRBuilder.extract_value(agg, index, name='')

     Extract the element at *index* of the
     :ref:`aggregate value <aggregate-types>` *agg*.

     * *index* may be an integer or a sequence of integers.
     * Indices must be constant.

* .. method:: IRBuilder.insert_value(agg, value, index, name='')

     Build a copy of :ref:`aggregate value <aggregate-types>`
     *agg* by setting the new *value* at *index*. The value for *index*
     can be of the same types as in :meth:`extract_value`.


Vector operations
-----------------

* .. method:: IRBuilder.extract_element(vector, idx, name='')

     Returns the *value* at position *idx*.

* .. method:: IRBuilder.insert_element(vector, value, idx, name='')

     Returns vector with ``vector[idx]`` replaced by ``value``.
     The result is undefined if the idx is larger or equal the vector length.

* .. method:: IRBuilder.shuffle_vector(vector1, vector2, mask, name='')

     Constructs a permutation of elements from *vector1* and *vector2*.
     Returns a new vector in the same length of *mask*.

     * *vector1* and *vector2* must have the same element type.
     * *mask* must be a constant vector of integer types.


Memory
-------

* .. method:: IRBuilder.alloca(typ, size=None, name='')

     Statically allocate a stack slot for *size* values of type
     *typ*. If *size* is not given, a stack slot for 1 value is
     allocated.

* .. method:: IRBuilder.load(ptr, name='', align=None)

     Load value from pointer *ptr*. If *align* is passed, it should
     be a Python integer specifying the guaranteed pointer
     alignment.

* .. method:: IRBuilder.store(value, ptr, align=None)

     Store *value* to pointer *ptr*. If *align* is passed, it should
     be a Python integer specifying the guaranteed pointer
     alignment.

* .. method:: IRBuilder.load_atomic(ptr, ordering, align, name='')

     Load value from pointer *ptr* as an atomic operation with the given
     *ordering*. *align* must be a Python integer specifying the guaranteed
     pointer alignment.

* .. method:: IRBuilder.store_atomic(value, ptr, ordering, align)

     Store *value* to pointer *ptr* as an atomic operation with the given
     *ordering*. *align* must be a Python integer specifying the guaranteed
     pointer alignment.

* .. method:: IRBuilder.gep(ptr, indices, inbounds=False, name='')

     The :ref:`getelementptr` instruction. Given a pointer *ptr*
     to an aggregate value, compute the address of the inner
     element given by the sequence of *indices*.

* .. method:: cmpxchg(ptr, cmp, val, ordering, failordering=None, name='')

     Atomic compare-and-swap at address *ptr*.

     * *cmp* is the value to compare the contents with.
     * *val* is the new value to be swapped into.
     * Optional *ordering* and *failordering* specify the memory
       model for this instruction.

* .. method:: atomic_rmw(op, ptr, val, ordering, name='')

     Atomic in-memory operation *op* at address *ptr*, with operand
     *val*.

     * The string *op* specifies the operation---for example,
       ``add`` or ``sub``.
     * The optional *ordering* specifies the memory model for this
       instruction.


Function call
---------------

.. method:: IRBuilder.call(fn, args, name='', cconv=None, tail=False, fastmath=())

   Call function *fn* with arguments *args*, a sequence of values.

   * *cconv* is the optional calling convention.
   * *tail*, if ``True``, is a hint for the optimizer to perform
     tail-call optimization.
   * *fastmath* is a string or a sequence of strings of names for
     `fast-math flags
     <http://llvm.org/docs/LangRef.html#fast-math-flags>`_.


Branches
-----------

The following methods are all :ref:`terminators <terminator>`:

* .. method:: IRBuilder.branch(target)

     Unconditional jump to the *target*, a :class:`Block`.

* .. method:: IRBuilder.cbranch(cond, truebr, falsebr)

     Conditional jump to either *truebr* or *falsebr*---both
     :class:`Block` instances---depending on *cond*, a value of
     type ``IntType(1)``. This instruction is a
     :class:`PredictableInstr`.

* .. method:: IRBuilder.ret(value)

     Return the *value* from the current function.

* .. method:: IRBuilder.ret_void()

     Return from the current function without a value.

* .. method:: IRBuilder.switch(value, default)

     Switch to different blocks based on the *value*. *default* is
     the block to switch to if no other block is matched.

     To add non-default targets, use the
     :meth:`~SwitchInstr.add_case` method on the return value.

* .. method:: IRBuilder.branch_indirect(address)

     Jump to the basic block with the address *address*, a value
     of type `IntType(8).as_pointer()`.

     To obtain a block address, use the
     :class:`BlockAddress` constant.

     To add all possible jump destinations, use
     the :meth:`~IndirectBranch.add_destination` method on the
     return value.


Exception handling
------------------

* .. method:: IRBuilder.invoke(self, fn, args, normal_to, unwind_to, name='', cconv=None, tail=False)

     Call function *fn* with arguments *args*, a sequence of values.

     * *cconv* is the optional calling convention.
     * *tail*, if ``True``, is a hint for the optimizer to perform
       tail-call optimization.

     If the function *fn* returns normally, control is transferred
     to *normal_to*. Otherwise, it is transferred to *unwind_to*,
     whose first non-phi instruction must be :class:`LandingPad`.

* .. method:: IRBuilder.landingpad(typ, personality, name='', cleanup=False)

     Describe which exceptions this basic block can handle.

     * *typ* specifies the return type of the landing pad. It is a
       structure with 2 pointer-sized fields.
     * *personality* specifies an exception personality function.
     * *cleanup* specifies whether control should always be
       transferred to this landing pad, even when no matching
       exception is caught.

     To add landing pad clauses, use the
     :meth:`~LandingPad.add_clause` method on the return value.

     There are 2 kinds of landing pad clauses:

     * A :class:`CatchClause`, which specifies a typeinfo for
       a single exception to be caught. The typeinfo is a value
       of type `IntType(8).as_pointer().as_pointer()`;

     * A :class:`FilterClause`, which specifies an array of
       typeinfos.

     Every landing pad must either contain at least 1 clause
     or be marked for cleanup.

     The semantics of a landing pad are entirely determined by
     the personality function. For details on the way LLVM
     handles landing pads in the optimizer, see
     `Exception handling in
     LLVM <http://llvm.org/docs/ExceptionHandling.html>`_.
     For details on the implementation of personality functions,
     see `Itanium exception handling
     ABI <https://itanium-cxx-abi.github.io/cxx-abi/abi-eh.html>`_.


* .. method:: IRBuilder.resume(landingpad)

     Resume an exception caught by *landingpad*. Used to indicate
     that the landing pad did not catch the exception after all,
     perhaps because it only performed cleanup.


Inline assembler
-----------------

* .. method:: IRBuilder.asm(ftype, asm, constraint, args, side_effect, name='')

     Add an inline assembler call instruction. For example, this
     is used in :meth:`load_reg` and :meth:`store_reg`.

     Arguments:

     * *ftype* is a function type specifying the inputs and output
       of the inline assembler call.
     * *asm* is the inline assembler snippet---for example,
       ``"mov $2, $0\nadd $1, $0"``. x86 inline ASM uses the
       AT&T syntax.
     * *constraint* defines the input/output constraints---for
       example ``=r,r,r``.
     * *args* is the list of inputs, as IR values.
     * *side_effect* is a boolean that specifies whether or not
       this instruction has side effects not visible in the
       constraint list.
     * *name* is the optional name of the returned LLVM value.

     For more information about these parameters, see the
     `official LLVM documentation <http://llvm.org/docs/LangRef.html#inline-asm-constraint-string>`_.

     EXAMPLE: Adding 2 64-bit values on x86::

        fty = FunctionType(IntType(64), [IntType(64),IntType(64)])
        add = builder.asm(fty, "mov $2, $0\nadd $1, $0", "=r,r,r",
                          (arg_0, arg_1), True, name="asm_add")


* .. method:: IRBuilder.load_reg(reg_type, reg_name, name='')

     Load a register value into an LLVM value.

     EXAMPLE: Obtaining the value of the ``rax`` register::

          builder.load_reg(IntType(64), "rax")

* .. method:: IRBuilder.store_reg(value, reg_type, reg_name, name='')

     Store an LLVM value inside a register.

     EXAMPLE: Storing ``0xAAAAAAAAAAAAAAAA`` into the ``rax``
     register::

        builder.store_reg(Constant(IntType(64), 0xAAAAAAAAAAAAAAAA), IntType(64), "rax")


Miscellaneous
--------------

* .. method:: IRBuilder.assume(cond)

     Let the LLVM optimizer assume that *cond*---a value of type
     ``IntType(1)``---is ``True``.

* .. method:: IRBuilder.unreachable()

     Mark an unreachable point in the code.
