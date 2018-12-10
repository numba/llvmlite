add_library(LLVMPYHello MODULE Hello.cpp)

llvm_map_components_to_libnames(llvm_libs demangle)
if (APPLE)
    target_link_libraries(LLVMPYHello PRIVATE ${llvm_libs} "-undefined dynamic_lookup")
else()
    target_link_libraries(LLVMPYHello PRIVATE ${llvm_libs})
endif()
