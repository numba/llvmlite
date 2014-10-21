#include "core.h"
#include "llvm-c/ExecutionEngine.h"
#include "llvm/IR/Module.h"
#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include <cstdio>

extern "C" {

void
LLVMPY_LinkInJIT() {
    LLVMLinkInJIT();
}

void
LLVMPY_LinkInMCJIT() {
    LLVMLinkInMCJIT();
}

void
LLVMPY_DisposeExecutionEngine(LLVMExecutionEngineRef EE)
{
    LLVMDisposeExecutionEngine(EE);
}

void
LLVMPY_AddModule(LLVMExecutionEngineRef EE,
              LLVMModuleRef M)
{
    LLVMAddModule(EE, M);
}

int
LLVMPY_RemoveModule(LLVMExecutionEngineRef EE,
                    LLVMModuleRef M,
                    char** OutError)
{
   return LLVMRemoveModule(EE, M, &M, OutError);
}

void
LLVMPY_FinalizeObject(LLVMExecutionEngineRef EE)
{
    llvm::unwrap(EE)->finalizeObject();
}


int
LLVMPY_CreateJITCompiler(LLVMExecutionEngineRef *OutEE,
                         LLVMModuleRef M,
                         unsigned OptLevel,
                         char **OutError)
{
    return LLVMCreateJITCompilerForModule(OutEE, M, OptLevel, OutError);
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

LLVMExecutionEngineRef
LLVMPY_CreateMCJITCompiler(LLVMModuleRef M,
                           LLVMTargetMachineRef TM,
                           int EmitDebug,
                           char **OutError)
{
    LLVMExecutionEngineRef ee = nullptr;

    llvm::EngineBuilder eb(llvm::unwrap(M));
    std::string err;
    eb.setErrorStr(&err);
    eb.setEngineKind(llvm::EngineKind::JIT);

    llvm::TargetOptions options;
    options.JITEmitDebugInfo = (bool)EmitDebug;
    options.TrapUnreachable = true;
//    options.NoFramePointerElim = true;
//    options.PrintMachineCode = false;

    eb.setTargetOptions(options);

    llvm::ExecutionEngine *engine = eb.create(llvm::unwrap(TM));

    if (!engine)
        *OutError = strdup(err.c_str());
    else
        ee = llvm::wrap(engine);
    return ee;
}

void*
LLVMPY_GetPointerToGlobal(LLVMExecutionEngineRef EE,
                          LLVMValueRef Global)
{
    return LLVMGetPointerToGlobal(EE, Global);
}

void
LLVMPY_AddGlobalMapping(LLVMExecutionEngineRef EE,
                        LLVMValueRef Global,
                        void *Addr)
{
    LLVMAddGlobalMapping(EE, Global, Addr);
}

LLVMTargetDataRef
LLVMPY_GetExecutionEngineTargetData(LLVMExecutionEngineRef EE)
{
    return LLVMGetExecutionEngineTargetData(EE);
}

} // end extern "C"
