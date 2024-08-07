.. _deprecation:

===================
Deprecation Notices
===================

This section contains information about deprecation of behaviours, features and
APIs that have become undesirable/obsolete. Any information about the schedule
for their deprecation and reasoning behind the changes, along with examples, is
provided.

Deprecation of Typed Pointers
=============================

The use of Typed Pointers is deprecated, and `Opaque Pointers <>`_ will be the
default (and eventually required) in a future llvmlite version.

Reason for deprecation
----------------------

llvmlite aims to move forward to newer LLVM versions, which will necessitate
switching to Opaque Pointers:

- In LLVM 15, `Opaque Pointers <>`_ are the default.
- In LLVM 16, Typed Pointers are only supported on a best-effort basis (and
  therefore may have bugs that go unfixed).
- In LLVM 17, support for Typed Pointers is removed.

Examples(s) of the impact
-------------------------

Code that uses llvmlite to work with pointers or to parse assembly that uses
pointers will break if not modified to use opaque pointers.

Schedule
--------

- In llvmlite 0.44, Opaque Pointers will be the default pointer kind.
- In llvmlite 0.45, support for Typed Pointers will be removed.

Recommendations
---------------

Binding layer:

`TargetData`

- Replace calls to `TargetData.get_pointee_abi_size` with calls to
  `TargetData.get_abi_size.
- Replace calls to `TargetData.get_pointee_abi_alignment` with calls to
  `TargetData.get_abi_alignment`.

Global Variables (binding) / Functions

- Replace use of the `GlobalValue.type` with `GlobalValue.global_value_type`

- Ensure that any IR passed to `parse_assembly` uses Opaque Pointers.


IR layer:

Modify calls to `ir.load`, `ir.load_atomic`, and `ir.gep` to pass in pointer
types.


Deprecation of `llvmlite.llvmpy` module
=======================================
The `llvmlite.llvmpy` module was originally created for compatibility with
`llvmpy`. As time has passed, that functionality was redesigned and put in
`llvmlite.ir` with `llvmlite.llvmpy` remaining as a compatibility layer. No
continued maintenance has ensured that it provides a matching API to `llvmpy`
and it provides no advantage over the `llvmlite.ir` module.

Reason for deprecation
----------------------
The functionality provided by `llvmlite.llvmpy` and its child modules is now
present in `llvmlite.ir`, so this module will be dropped.

Example(s) of the impact
------------------------
Code that imports `llvmlite.llvmpy`, `llvmlite.llvmpy.core` or
`llvmlite.llvmpy.passes` will break.

Schedule
--------
The feature change was implemented as follows:

* v0.39 module is deprecated
* v0.40 module is removed

Recommendations
---------------
Since similar functionality already exists in `llvmlite.ir`, the transition
path is relatively short:

- replace `llvmlite.llvmpy.core.Builder` with `llvmlite.ir.IRBuilder`
- replace `llvmlite.llvmpy.core.Builder.icmp` with
  `llvmlite.ir.IRBuilder.icmp_signed` and `icmp_unsigned`, as appropriate
- replace `llvmlite.llvmpy.core.Builder.fcmp` with
  `llvmlite.ir.IRBuilder.fcmp_ordered` and `fcmp_unordered`, as appropriate
- replace calls to the static methods of `llvmlite.llvmpy.core.Type` with the
  constructors provided in `llvmlite.ir` (_e.g._, `Type.int(8)` with
  `IntType(8)`)
- Replace calls to the static methods of `llvmlite.llvmpy.core.Constant` with
  calls to the constructor of `llvmlite.ir.Constant` or
  `llvmlite.ir.Constant.literal_struct`, as appropriate. Note that `stringz`
  and `array` have no direct equivalents.
- replace `llvmlite.llvmpy.core.Module`, `Function`, `MetaDataString`,
  `InlineAsm` with the classes of the same name in `llvmlite.ir.`
- replace `llvmlite.llvmpy.core.MetaData.get` with
  `llvmlite.ir.Module.add_metadata`
- replace `llvmlite.llvmpy.core.Function.intrinsic` with
  `llvmlite.ir.Module.declare_intrinsic`
- for `llvmlite.llvmpy.passes`, create the pass manager directly using
  `llvmlite.binding`

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
