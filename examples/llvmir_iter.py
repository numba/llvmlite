import llvmlite.binding as llvm
ir = r'''
    ; ModuleID = '<string>'
    target triple = "unknown-unknown-unknown"
    %struct.glob_type = type { i64, [2 x i64] }

    @glob = global i32 0
    @glob_b = global i8 0
    @glob_f = global float 1.5
    @glob_struct = global %struct.glob_type {i64 0, [2 x i64] [i64 0, i64 0]}

    define i32 @sum(i32 %.1, i32 %.2) {
      %.3 = add i32 %.1, %.2
      %.4 = add i32 0, %.3
      ret i32 %.4
    }

    define void @foo() {
      call void asm sideeffect "nop", ""()
      ret void
    }

    declare void @a_readonly_func(i8 *) readonly
'''

m = llvm.parse_assembly(ir)

for f in m.functions:
    print(f'Function: {f.name}/`{f.type}`')
    assert f.module is m
    assert f.function is None
    assert f.block is None
    assert f.is_function and not (f.is_block or f.is_instruction)
    print(f'Function attributes: {list(f.attributes)}')
    for a in f.arguments:
        print(f'Argument: {a.name}/`{a.type}`')
        print(f'Argument attributes: {list(a.attributes)}')
    for b in f.blocks:
        print(f'Block: {b.name}/`{b.type}`\n{b}\nEnd of Block')
        assert b.module is m
        assert b.function is f
        assert b.block is None
        assert b.is_block and not (b.is_function or b.is_instruction)
        for i in b.instructions:
            print(f'Instruction: {i.name}/`{i.opcode}`/`{i.type}`: `{i}`')
            print(f'Attributes: {list(i.attributes)}')
            assert i.module is m
            assert i.function is f
            assert i.block is b
            assert i.is_instruction and not (i.is_function or i.is_block)
            for o in i.operands:
                print(f'Operand: {o.name}/{o.type}')

for g in m.global_variables:
    print(f'Global: {g.name}/`{g.type}`')
    assert g.is_global
    print(f'Attributes: {list(g.attributes)}')
    print(g)
