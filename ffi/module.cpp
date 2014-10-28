#include <string>
#include "llvm-c/Core.h"
#include "llvm-c/Analysis.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Module.h"
#include "core.h"


struct GlobalsIterator {
    typedef llvm::Module::global_iterator iterator;
    iterator cur;
    iterator end;

    GlobalsIterator(iterator cur, iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueGlobalsIterator;
typedef OpaqueGlobalsIterator* LLVMGlobalsIteratorRef;


namespace llvm {

LLVMGlobalsIteratorRef
wrap(GlobalsIterator* GI){
    return reinterpret_cast<LLVMGlobalsIteratorRef>(GI);
}

GlobalsIterator*
unwrap(LLVMGlobalsIteratorRef GI){
    return reinterpret_cast<GlobalsIterator*>(GI);
}

}  // end namespace llvm


extern "C" {

API_EXPORT(void)
LLVMPY_DisposeModule(LLVMModuleRef m) {
    return LLVMDisposeModule(m);
}

API_EXPORT(void)
LLVMPY_PrintModuleToString(LLVMModuleRef M,
                           const char **outstr)
{
    using namespace llvm;
    std::string buf;
    raw_string_ostream os(buf);
    unwrap(M)->print(os, NULL);
    os.flush();
    *outstr = LLVMPY_CreateString(buf.c_str());
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedFunction(LLVMModuleRef M,
                     const char *Name)
{
    return LLVMGetNamedFunction(M, Name);
}

API_EXPORT(LLVMValueRef)
LLVMPY_GetNamedGlobalVariable(LLVMModuleRef M,
                              const char *Name)
{
    using namespace llvm;
    return wrap(unwrap(M)->getGlobalVariable(Name));
}


API_EXPORT(int)
LLVMPY_VerifyModule(LLVMModuleRef M, char **OutMsg)
{
    return LLVMVerifyModule(M, LLVMReturnStatusAction, OutMsg);
}

API_EXPORT(void)
LLVMPY_GetDataLayout(LLVMModuleRef M,
                     const char **DL)
{
    *DL = LLVMGetDataLayout(M);
}


API_EXPORT(void)
LLVMPY_SetDataLayout(LLVMModuleRef M,
                     const char *DL)
{
    LLVMSetDataLayout(M, DL);
}


API_EXPORT(LLVMGlobalsIteratorRef)
LLVMPY_ModuleGlobalIter(LLVMModuleRef M)
{
    using namespace llvm;
    Module* mod = unwrap(M);
    return wrap(new GlobalsIterator(mod->global_begin(),
                                    mod->global_end()));
}


/*
Returns NULL if we are at the end
*/
API_EXPORT(LLVMValueRef)
LLVMPY_GlobalIterNext(LLVMGlobalsIteratorRef GI)
{
    using namespace llvm;
    GlobalsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeGlobalIter(LLVMGlobalsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}


} // end extern "C"
