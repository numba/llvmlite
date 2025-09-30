"""
Demonstration of llvmlite's New Pass Manager API.

This example shows how to use the new pass manager to optimize LLVM IR.
Comments show the equivalent legacy pass manager approach for comparison.
"""

import llvmlite.binding as llvm

# Initialize LLVM
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

# Create a module with some sample IR
module = llvm.parse_assembly("""
define i32 @test_function(i32 %x, i32 %y) {
entry:
    %z = add i32 %x, %y
    %w = add i32 %z, 0    ; This can be optimized away
    %t = mul i32 %w, 1    ; This can also be optimized away
    ret i32 %t
}

define i32 @unused_function() {
entry:
    ret i32 42
}
""")

print("Original IR:")
print(str(module))

# Create target machine
target = llvm.Target.from_default_triple()
target_machine = target.create_target_machine()

# NEW PASS MANAGER API:
# Create pipeline tuning options with optimization settings
pto = llvm.create_pipeline_tuning_options(speed_level=2, size_level=0)
# LEGACY EQUIVALENT:
# pmb = llvm.PassManagerBuilder()
# pmb.opt_level = 2
# pmb.size_level = 0

# Optionally customize the tuning options
pto.loop_vectorization = True
pto.slp_vectorization = True
pto.loop_unrolling = True
# LEGACY EQUIVALENT:
# pmb.loop_vectorize = True
# pmb.slp_vectorize = True
# pmb.disable_unroll_loops = False

# Create the pass builder
pass_builder = llvm.create_pass_builder(target_machine, pto)
# LEGACY EQUIVALENT: PassManagerBuilder handles this internally

# Get a populated module pass manager
mpm = pass_builder.getModulePassManager()
# LEGACY EQUIVALENT:
# mpm = llvm.ModulePassManager()
# pmb.populate(mpm)

# Run the optimization passes
mpm.run(module, pass_builder)
# LEGACY EQUIVALENT:
# changed = mpm.run(module)

print("\nOptimized IR:")
print(str(module))

# For function-level optimizations, you can also use:
fpm = pass_builder.getFunctionPassManager()
# LEGACY EQUIVALENT:
# fpm = llvm.FunctionPassManager(module)
# pmb.populate(fpm)
# fpm.initialize()

for function in module.functions:
    fpm.run(function, pass_builder)
# LEGACY EQUIVALENT:
# for function in module.functions:
#     fpm.run(function)
# fpm.finalize()  # Call after all functions are processed
