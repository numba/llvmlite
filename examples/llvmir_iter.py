import llvmlite.binding as llvm
from llvmir import module

ir = str(module)
m = llvm.parse_assembly(ir)

for f in m.functions:
    print(f'Function: {f.name}/`{f.type}`')
    assert f.module is m
    assert f.function is None
    assert f.block is None
    assert f.is_function and not (f.is_block or f.is_instruction)
    for b in f.blocks:
        print(f'Block: {b.name}/`{b.type}`\n{b}\nEnd of Block')
        assert b.module is m
        assert b.function is f
        assert b.block is None
        assert b.is_block and not (b.is_function or b.is_instruction)
        for i in b.instructions:
            print(f'Instruction: {i.name}/`{i.type}`: `{i}`')
            assert i.module is m
            assert i.function is f
            assert i.block is b
            assert i.is_instruction and not (i.is_function or i.is_block)
