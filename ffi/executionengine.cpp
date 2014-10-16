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

int
LLVMPY_CreateMCJITCompilerCustom(LLVMExecutionEngineRef *OutEE,
                                 LLVMModuleRef M,
                                 int Opt,
                                 const char *RelocModel,
                                 int EmitDebug,
                                 char **OutError)
{
    llvm::EngineBuilder eb(llvm::unwrap(M));
    std::string err;
    eb.setErrorStr(&err);
    eb.setEngineKind(llvm::EngineKind::JIT);
    eb.setOptLevel((llvm::CodeGenOpt::Level)Opt);

    std::string rm = RelocModel;
    if (rm == "static") {
        eb.setRelocationModel(llvm::Reloc::Default);
    } else if (rm == "pic") {
        eb.setRelocationModel(llvm::Reloc::PIC_);
    } else if (rm == "dynamicnopic") {
        eb.setRelocationModel(llvm::Reloc::DynamicNoPIC);
    }

    llvm::TargetOptions options;
    options.JITEmitDebugInfo = (bool)EmitDebug;
    options.TrapUnreachable = true;
//    options.NoFramePointerElim = true;
//    options.PrintMachineCode = false;

    eb.setTargetOptions(options);

    llvm::ExecutionEngine *engine = eb.create();

    if (!engine) {
        *OutError = strdup(err.c_str());
        return 1;
    } else {
        *OutEE = llvm::wrap(engine);
        return 0;
    }
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


} // end extern "C"
