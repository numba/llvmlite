from llvmlite import binding as llvm
from llvmlite import ir as lc

llvm.initialize()
llvm.initialize_native_target()

mod = lc.Module()
mod.triple = llvm.get_default_triple()
func = lc.Function(mod, lc.FunctionType(lc.VoidType(), lc.IntType(32)),
                   name='foo')
builder = lc.IRBuilder(func.append_basic_block())
builder.ret_void()

print(mod)

mod = llvm.parse_assembly(str(mod))

mod.verify()
print(repr(mod))
print(mod)

pmb = llvm.create_pass_manager_builder()
pmb.close()

ee = llvm.create_jit_compiler(mod)
func = mod.get_function(name="foo")
print(func, ee.get_pointer_to_global(func))
ee.close()

llvm.shutdown()

