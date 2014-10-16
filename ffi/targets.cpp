#include "core.h"
#include "llvm-c/Target.h"
#include "llvm/Support/Host.h"
#include <cstdio>


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

} // end extern "C"
