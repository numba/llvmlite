import llvmlite.binding as llvm
from llvmir import module

ir = str(module)
m = llvm.parse_assembly(ir)

for f in m.functions:
    print(f.name)
    for b in f.blocks:
        print(type(b))
        for i in b.instructions:
            print(type(i))
