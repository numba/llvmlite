.. _deprecation:

===================
Deprecation Notices
===================

This section contains information about deprecation of behaviours, features and
APIs that have become undesirable/obsolete. Any information about the schedule
for their deprecation and reasoning behind the changes, along with examples, is
provided.

Deprecation of use of memset/memcpy llvm intrinsic with specified alignment
===========================================================================
From LLVM 7 onward the `memset <https://releases.llvm.org/7.0.0/docs/LangRef.html#llvm-memset-intrinsics>`_
and `memcpy <https://releases.llvm.org/7.0.0/docs/LangRef.html#llvm-memcpy-intrinsic>`_
intrinsics dropped the use of an alignment, specified as the third argument, and
instead use the alignment of the first argument for this purpose. Specifying
the alignment in third argument continued to work as LLVM auto-updates this use
case.

Reason for deprecation
----------------------
LLVM has changed the behaviour of the previously mentioned intrinsics, and so as
to increase compatibility with future releases of LLVM, llvmlite is adapting to
match.

Example(s) of the impact
------------------------

As of 0.30 the following worked::

    from llvmlite import ir

    bit = ir.IntType(1)
    int8 = ir.IntType(8)
    int32 = ir.IntType(32)
    int64 = ir.IntType(64)
    int8ptr = int8.as_pointer()

    mod = ir.Module()
    fnty = ir.FunctionType(int32, ())
    func = ir.Function(mod, fnty, "some_function")
    block = func.append_basic_block('some_block')
    builder = ir.IRBuilder(block)

    some_address = int64(0xdeaddead)
    dest = builder.bitcast(some_address, int8ptr)
    value = int8(0xa5)
    memset = mod.declare_intrinsic('llvm.memset', [int8ptr, int32])
    memcpy = mod.declare_intrinsic('llvm.memcpy', [int8ptr, int8ptr, int32])

    # NOTE: 5 argument call site (dest, value, length, align, isvolatile)
    builder.call(memset, [dest, value, int32(10), int32(0), bit(0)])

    some_other_address = int64(0xcafecafe)
    src = builder.bitcast(some_other_address, int8ptr)

    # NOTE: 5 argument call site (dest, src, length, align, isvolatile)
    builder.call(memcpy, [dest, src, int32(10), int32(0), bit(0)])

    builder.ret(int32(0))
    print(str(mod))


From 0.31 onwards only the following works::

    from llvmlite import ir

    bit = ir.IntType(1)
    int8 = ir.IntType(8)
    int32 = ir.IntType(32)
    int64 = ir.IntType(64)
    int8ptr = int8.as_pointer()

    mod = ir.Module()
    fnty = ir.FunctionType(int32, ())
    func = ir.Function(mod, fnty, "some_function")
    block = func.append_basic_block('some_block')
    builder = ir.IRBuilder(block)

    some_address = int64(0xdeaddead)
    dest = builder.bitcast(some_address, int8ptr)
    value = int8(0xa5)
    memset = mod.declare_intrinsic('llvm.memset', [int8ptr, int32])
    memcpy = mod.declare_intrinsic('llvm.memcpy', [int8ptr, int8ptr, int32])

    # NOTE: 4 argument call site (dest, value, length, isvolatile)
    builder.call(memset, [dest, value, int32(10), bit(0)])

    some_other_address = int64(0xcafecafe)
    src = builder.bitcast(some_other_address, int8ptr)

    # NOTE: 4 argument call site (dest, src, length, isvolatile)
    builder.call(memcpy, [dest, src, int32(10), bit(0)])

    builder.ret(int32(0))
    print(str(mod))


Schedule
--------
The feature change was implemented as follows:

* v0.30 was the last release to support an alignment specified as the third
  argument (5 argument style).
* v0.31 onwards supports the 4 argument style call only.


Recommendations
---------------
Projects that need/rely on the deprecated behaviour should pin their dependency
on llvmlite to a version prior to removal of this behaviour.
