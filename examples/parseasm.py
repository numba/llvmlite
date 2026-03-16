from llvmlite import binding as llvm
from llvmlite import ir as lc

llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

mod = lc.Module()
mod.triple = llvm.get_default_triple()
func = lc.Function(mod, lc.FunctionType(lc.VoidType(), [lc.IntType(32)]),
                   name='foo')
builder = lc.IRBuilder(func.append_basic_block())
builder.ret_void()

print(mod)

mod = llvm.parse_assembly(str(mod))

mod.verify()
print(repr(mod))
print(mod)

tm = llvm.Target.from_default_triple().create_target_machine()
pto = llvm.create_pipeline_tuning_options()

with llvm.create_new_module_pass_manager() as pm:
    pb = llvm.create_pass_builder(tm, pto)
    pm.run(mod, pb)

print(mod)

ee = llvm.create_mcjit_compiler(mod, tm)
func = mod.get_function("foo")
print(func, ee.get_function_address("foo"))
ee.close()

llvm.shutdown()

