#include "core.h"
#include "llvm-c/ExecutionEngine.h"
#include "llvm/IR/Module.h"
#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include "llvm/Support/Memory.h"
#include <cstdio>

extern "C" {

API_EXPORT(void)
LLVMPY_LinkInMCJIT() {
    LLVMLinkInMCJIT();
}

API_EXPORT(void)
LLVMPY_DisposeExecutionEngine(LLVMExecutionEngineRef EE)
{
    LLVMDisposeExecutionEngine(EE);
}

API_EXPORT(void)
LLVMPY_AddModule(LLVMExecutionEngineRef EE,
              LLVMModuleRef M)
{
    LLVMAddModule(EE, M);
}

API_EXPORT(int)
LLVMPY_RemoveModule(LLVMExecutionEngineRef EE,
                    LLVMModuleRef M,
                    char** OutError)
{
   return LLVMRemoveModule(EE, M, &M, OutError);
}

API_EXPORT(void)
LLVMPY_FinalizeObject(LLVMExecutionEngineRef EE)
{
    llvm::unwrap(EE)->finalizeObject();
}


// wrap/unwrap for LLVMTargetMachineRef.
// Ripped from lib/Target/TargetMachineC.cpp.

namespace llvm {
    inline TargetMachine *unwrap(LLVMTargetMachineRef P) {
      return reinterpret_cast<TargetMachine*>(P);
    }
    inline LLVMTargetMachineRef wrap(const TargetMachine *P) {
      return
        reinterpret_cast<LLVMTargetMachineRef>(const_cast<TargetMachine*>(P));
    }
}


static
LLVMExecutionEngineRef
create_execution_engine(LLVMModuleRef M,
                        LLVMTargetMachineRef TM,
                        char **OutError
                        )
{
    LLVMExecutionEngineRef ee = nullptr;

    llvm::EngineBuilder eb(std::unique_ptr<llvm::Module>(llvm::unwrap(M)));
    std::string err;
    eb.setErrorStr(&err);
    eb.setEngineKind(llvm::EngineKind::JIT);

    /* EngineBuilder::create loads the current process symbols */
    llvm::ExecutionEngine *engine = eb.create(llvm::unwrap(TM));

    if (!engine)
        *OutError = strdup(err.c_str());
    else
        ee = llvm::wrap(engine);
    return ee;
}

API_EXPORT(LLVMExecutionEngineRef)
LLVMPY_CreateMCJITCompiler(LLVMModuleRef M,
                           LLVMTargetMachineRef TM,
                           char **OutError)
{
    return create_execution_engine(M, TM, OutError);
}

API_EXPORT(void *)
LLVMPY_GetPointerToGlobal(LLVMExecutionEngineRef EE,
                          LLVMValueRef Global)
{
    return LLVMGetPointerToGlobal(EE, Global);
}

API_EXPORT(uint64_t)
LLVMPY_GetGlobalValueAddress(LLVMExecutionEngineRef EE,
                             const char *Name)
{
    return LLVMGetGlobalValueAddress(EE, Name);
}

API_EXPORT(uint64_t)
LLVMPY_GetFunctionAddress(LLVMExecutionEngineRef EE,
                          const char *Name)
{
    return LLVMGetFunctionAddress(EE, Name);
}

API_EXPORT(void)
LLVMPY_AddGlobalMapping(LLVMExecutionEngineRef EE,
                        LLVMValueRef Global,
                        void *Addr)
{
    LLVMAddGlobalMapping(EE, Global, Addr);
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_GetExecutionEngineTargetData(LLVMExecutionEngineRef EE)
{
    return LLVMGetExecutionEngineTargetData(EE);
}

API_EXPORT(int)
LLVMPY_TryAllocateExecutableMemory(void)
{
    using namespace llvm::sys;
    std::error_code ec;
    MemoryBlock mb = Memory::allocateMappedMemory(4096, nullptr,
                                                  Memory::MF_READ |
                                                  Memory::MF_WRITE,
                                                  ec);
    if (!ec) {
        ec = Memory::protectMappedMemory(mb, Memory::MF_READ | Memory::MF_EXEC);
        (void) Memory::releaseMappedMemory(mb);  /* Should always succeed */
    }
    return ec.value();
}

} // end extern "C"
