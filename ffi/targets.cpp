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
LLVMPY_GetTargetFromTriple (const char *Triple, const char **ErrOut)
{
    char *ErrorMessage;
    LLVMTargetRef T;
    if ( 0 != LLVMGetTargetFromTriple(Triple, &T, &ErrorMessage) ) {
        *ErrOut = LLVMPY_CreateString(ErrorMessage);
        LLVMDisposeMessage(ErrorMessage);
        return NULL;
    }
    return T;
}

LLVMTargetMachineRef
LLVMPY_CreateTargetMachine (   LLVMTargetRef T,
                               const char *Triple,
                               const char *CPU,
                               const char *Features,
                               int         OL,
                               const char *RM,
                               const char *CM  )
{
    LLVMCodeGenOptLevel cgol;
    switch(OL) {
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
    if ( strcmp(CM, "jitdefault") == 0 ){
        cm = LLVMCodeModelJITDefault;
    } else if ( strcmp(CM, "small") == 0 ){
        cm = LLVMCodeModelSmall;
    } else if ( strcmp(CM, "kernel") == 0 ){
        cm = LLVMCodeModelKernel;
    } else if ( strcmp(CM, "Medium") == 0 ){
        cm = LLVMCodeModelMedium;
    } else if ( strcmp(CM, "Large") == 0 ){
        cm = LLVMCodeModelLarge;
    } else {
        cm = LLVMCodeModelDefault;
    }

    LLVMRelocMode rm;
    if ( strcmp(RM, "static") == 0 ) {
        rm = LLVMRelocStatic;
    } else if ( strcmp(RM, "pic") == 0 ) {
        rm = LLVMRelocPIC;
    } else if ( strcmp(RM, "dynamicnopic") == 0 ) {
        rm = LLVMRelocDynamicNoPic;
    } else {
        rm = LLVMRelocDefault;
    }

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
