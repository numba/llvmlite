add_library(LLVMPYHello MODULE Hello.cpp)

llvm_map_components_to_libnames(llvm_libs demangle)
target_link_libraries(LLVMPYHello PRIVATE ${llvm_libs})
