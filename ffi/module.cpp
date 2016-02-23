#include <string>
#include <clocale>
#include "llvm-c/Core.h"
#include "llvm-c/Analysis.h"
#include "llvm/IR/Module.h"
#include "core.h"


/* An iterator around a module's globals, including the stop condition */
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


/* An iterator around a module's functions, including the stop condition */
struct FunctionsIterator {
    typedef llvm::Module::const_iterator const_iterator;
    const_iterator cur;
    const_iterator end;

    FunctionsIterator(const_iterator cur, const_iterator end)
        :cur(cur), end(end)
    { }
};

struct OpaqueFunctionsIterator;
typedef OpaqueFunctionsIterator* LLVMFunctionsIteratorRef;


//
// Local helper functions
//

namespace llvm {

static LLVMGlobalsIteratorRef
wrap(GlobalsIterator* GI){
    return reinterpret_cast<LLVMGlobalsIteratorRef>(GI);
}

static GlobalsIterator*
unwrap(LLVMGlobalsIteratorRef GI){
    return reinterpret_cast<GlobalsIterator*>(GI);
}

static LLVMFunctionsIteratorRef
wrap(FunctionsIterator* GI){
    return reinterpret_cast<LLVMFunctionsIteratorRef>(GI);
}

static FunctionsIterator*
unwrap(LLVMFunctionsIteratorRef GI){
    return reinterpret_cast<FunctionsIterator *>(GI);
}

}  // end namespace llvm


//
// Exported API
//

extern "C" {

API_EXPORT(void)
LLVMPY_DisposeModule(LLVMModuleRef m) {
    return LLVMDisposeModule(m);
}

API_EXPORT(void)
LLVMPY_PrintModuleToString(LLVMModuleRef M,
                           const char **outstr)
{
    // Change the locale to en_US before calling LLVM to print the module
    // due to a LLVM bug https://llvm.org/bugs/show_bug.cgi?id=12906
    char *old_locale = strdup(setlocale(LC_ALL, NULL));
    setlocale(LC_ALL, "C");

    *outstr = LLVMPrintModuleToString(M);

    // Revert locale
    setlocale(LC_ALL, old_locale);
    free(old_locale);
}

API_EXPORT(const char *)
LLVMPY_GetModuleName(LLVMModuleRef M)
{
    return llvm::unwrap(M)->getModuleIdentifier().c_str();
}

API_EXPORT(void)
LLVMPY_SetModuleName(LLVMModuleRef M, const char *Name)
{
    llvm::unwrap(M)->setModuleIdentifier(Name);
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


API_EXPORT(void)
LLVMPY_GetTarget(LLVMModuleRef M,
                 const char **Triple)
{
    *Triple = LLVMGetTarget(M);
}


API_EXPORT(void)
LLVMPY_SetTarget(LLVMModuleRef M,
                 const char *Triple)
{
    LLVMSetTarget(M, Triple);
}

// Iteration APIs

API_EXPORT(LLVMGlobalsIteratorRef)
LLVMPY_ModuleGlobalsIter(LLVMModuleRef M)
{
    using namespace llvm;
    Module* mod = unwrap(M);
    return wrap(new GlobalsIterator(mod->global_begin(),
                                    mod->global_end()));
}

API_EXPORT(LLVMFunctionsIteratorRef)
LLVMPY_ModuleFunctionsIter(LLVMModuleRef M)
{
    using namespace llvm;
    Module* mod = unwrap(M);
    return wrap(new FunctionsIterator(mod->begin(),
                                      mod->end()));
}


/*
  These functions return NULL if we are at the end
*/
API_EXPORT(LLVMValueRef)
LLVMPY_GlobalsIterNext(LLVMGlobalsIteratorRef GI)
{
    using namespace llvm;
    GlobalsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(LLVMValueRef)
LLVMPY_FunctionsIterNext(LLVMFunctionsIteratorRef GI)
{
    using namespace llvm;
    FunctionsIterator* iter = unwrap(GI);
    if (iter->cur != iter->end) {
        return wrap(&*iter->cur++);
    } else {
        return NULL;
    }
}

API_EXPORT(void)
LLVMPY_DisposeGlobalsIter(LLVMGlobalsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(void)
LLVMPY_DisposeFunctionsIter(LLVMFunctionsIteratorRef GI)
{
    delete llvm::unwrap(GI);
}

API_EXPORT(LLVMModuleRef)
LLVMPY_CloneModule(LLVMModuleRef M)
{
    return LLVMCloneModule(M);
}

} // end extern "C"
