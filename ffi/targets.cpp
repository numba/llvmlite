#include "core.h"
#include "llvm-c/Target.h"
#include "llvm/Support/Host.h"
#include "llvm-c/TargetMachine.h"
//#include "llvm/Support/TargetRegistry.h"
//#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include <cstdio>
#include <cstring>


extern "C" {

void
LLVMPY_GetDefaultTargetTriple(const char **Out){
    using namespace llvm;
    *Out = LLVMPY_CreateString(sys::getDefaultTargetTriple().c_str());
}

LLVMTargetDataRef
LLVMPY_CreateTargetData(const char *StringRep)
{
    return LLVMCreateTargetData(StringRep);
}

void
LLVMPY_AddTargetData(LLVMTargetDataRef TD,
                     LLVMPassManagerRef PM)
{
    LLVMAddTargetData(TD, PM);
}


//// Nothing is creating a TargetLibraryInfo
//    void
//    LLVMPY_AddTargetLibraryInfo(LLVMTargetLibraryInfoRef TLI,
//                                LLVMPassManagerRef PM)
//    {
//        LLVMAddTargetLibraryInfo(TLI, PM);
//    }

void
LLVMPY_CopyStringRepOfTargetData(LLVMTargetDataRef TD, char** Out)
{
    *Out = LLVMCopyStringRepOfTargetData(TD);
}

void
LLVMPY_DisposeTargetData(LLVMTargetDataRef TD)
{
    LLVMDisposeTargetData(TD);
}


unsigned long long
LLVMPY_ABISizeOfType(LLVMTargetDataRef TD, LLVMTypeRef Ty)
{
    return LLVMABISizeOfType(TD, Ty);
}


LLVMTargetRef
LLVMPY_GetTargetFromTriple(const char *Triple, const char **ErrOut)
{
    char *ErrorMessage;
    LLVMTargetRef T;
    if (LLVMGetTargetFromTriple(Triple, &T, &ErrorMessage)) {
        *ErrOut = LLVMPY_CreateString(ErrorMessage);
        LLVMDisposeMessage(ErrorMessage);
        return NULL;
    }
    return T;
}

LLVMTargetMachineRef
LLVMPY_CreateTargetMachine(LLVMTargetRef T,
                           const char *Triple,
                           const char *CPU,
                           const char *Features,
                           int         OptLevel,
                           const char *RelocModel,
                           const char *CodeModel)
{
    LLVMCodeGenOptLevel cgol;
    switch(OptLevel) {
    case 0:
        cgol = LLVMCodeGenLevelNone;
        break;
    case 1:
        cgol = LLVMCodeGenLevelLess;
        break;
    case 3:
        cgol = LLVMCodeGenLevelAggressive;
        break;
    case 2:
    default:
        cgol = LLVMCodeGenLevelDefault;
    }

    LLVMCodeModel cm;
    std::string cms(CodeModel);
    if (cms == "jitdefault")
        cm = LLVMCodeModelJITDefault;
    else if (cms == "small")
        cm = LLVMCodeModelSmall;
    else if (cms == "kernel")
        cm = LLVMCodeModelKernel;
    else if (cms == "medium")
        cm = LLVMCodeModelMedium;
    else if (cms == "large")
        cm = LLVMCodeModelLarge;
    else
        cm = LLVMCodeModelDefault;

    LLVMRelocMode rm;
    std::string rms(RelocModel);
    if (rms == "static")
        rm = LLVMRelocStatic;
    else if (rms == "pic")
        rm = LLVMRelocPIC;
    else if (rms == "dynamicnopic")
        rm = LLVMRelocDynamicNoPic;
    else
        rm = LLVMRelocDefault;

    return LLVMCreateTargetMachine(T, Triple, CPU, Features, cgol, rm, cm);
}


void
LLVMPY_DisposeTargetMachine(LLVMTargetMachineRef TM)
{
    return LLVMDisposeTargetMachine(TM);
}


LLVMMemoryBufferRef
LLVMPY_TargetMachineEmitToMemory (
    LLVMTargetMachineRef TM,
    LLVMModuleRef M,
    int use_object,
    const char ** ErrOut
    )
{
    LLVMCodeGenFileType filetype = LLVMAssemblyFile;
    if (use_object) filetype = LLVMObjectFile;

    char *ErrorMessage;
    LLVMMemoryBufferRef BufOut;
    int err = LLVMTargetMachineEmitToMemoryBuffer(TM, M, filetype,
                                                  &ErrorMessage,
                                                  &BufOut);
    if (err) {
        *ErrOut = LLVMPY_CreateString(ErrorMessage);
        LLVMDisposeMessage(ErrorMessage);
        return NULL;
    }

    return BufOut;
}

const void*
LLVMPY_GetBufferStart(LLVMMemoryBufferRef MB)
{
    return LLVMGetBufferStart(MB);
}

size_t
LLVMPY_GetBufferSize(LLVMMemoryBufferRef MB)
{
    return LLVMGetBufferSize(MB);
}

void
LLVMPY_DisposeMemoryBuffer(LLVMMemoryBufferRef MB)
{
    return LLVMDisposeMemoryBuffer(MB);
}




} // end extern "C"
