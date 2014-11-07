#include "core.h"
#include "llvm-c/ExecutionEngine.h"
#include "llvm/IR/Module.h"
#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include <cstdio>

extern "C" {

API_EXPORT(void)
LLVMPY_LinkInJIT() {
    LLVMLinkInJIT();
}

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
                        char **OutError,
                        bool useMCJIT )
{
    LLVMExecutionEngineRef ee = nullptr;

    llvm::EngineBuilder eb(llvm::unwrap(M));
    std::string err;
    eb.setErrorStr(&err);
    eb.setEngineKind(llvm::EngineKind::JIT);
    eb.setUseMCJIT(useMCJIT);

    /* EngineBuilder::create loads the current process symbols */
    llvm::ExecutionEngine *engine = eb.create(llvm::unwrap(TM));

    if (!engine)
        *OutError = strdup(err.c_str());
    else
        ee = llvm::wrap(engine);
    return ee;
}

API_EXPORT(int)
LLVMPY_CreateJITCompiler(LLVMExecutionEngineRef *OutEE,
                         LLVMModuleRef M,
                         unsigned OptLevel,
                         char **OutError)
{
    return LLVMCreateJITCompilerForModule(OutEE, M, OptLevel, OutError);
}

API_EXPORT(LLVMExecutionEngineRef)
LLVMPY_CreateJITCompilerWithTM(LLVMModuleRef M,
                           LLVMTargetMachineRef TM,
                           char **OutError)
{
    return create_execution_engine(M, TM, OutError, false);
}

API_EXPORT(LLVMExecutionEngineRef)
LLVMPY_CreateMCJITCompiler(LLVMModuleRef M,
                           LLVMTargetMachineRef TM,
                           char **OutError)
{
    return create_execution_engine(M, TM, OutError, true);
}

API_EXPORT(void *)
LLVMPY_GetPointerToGlobal(LLVMExecutionEngineRef EE,
                          LLVMValueRef Global)
{
    return LLVMGetPointerToGlobal(EE, Global);
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

} // end extern "C"
