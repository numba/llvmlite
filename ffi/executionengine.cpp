#include "core.h"

#include "llvm-c/ExecutionEngine.h"

#include "llvm/IR/Module.h"
#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include "llvm/ExecutionEngine/ObjectCache.h"
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


//
// Object cache
//

typedef void (*ObjectCacheNotifyFunc)(LLVMModuleRef, const char *, size_t);
typedef void (*ObjectCacheGetObjectFunc)(LLVMModuleRef, const char **, size_t *);


class LLVMPYObjectCache : public llvm::ObjectCache {
public:
    LLVMPYObjectCache(ObjectCacheNotifyFunc notify_func,
                      ObjectCacheGetObjectFunc getobject_func)
    : notify_func(notify_func), getobject_func(getobject_func)
    {
    }

    virtual void notifyObjectCompiled(const llvm::Module *M,
                                      llvm::MemoryBufferRef MBR)
    {
        if (notify_func)
            notify_func(llvm::wrap(M), MBR.getBufferStart(), MBR.getBufferSize());
    }

    // MCJIT will call this function before compiling any module
    // MCJIT takes ownership of both the MemoryBuffer object and the memory
    // to which it refers.
    virtual std::unique_ptr<llvm::MemoryBuffer> getObject(const llvm::Module* M)
    {
        const char *buf_ptr = nullptr;
        size_t buf_len = 0;
        std::unique_ptr<llvm::MemoryBuffer> res = nullptr;

        if (getobject_func) {
            getobject_func(llvm::wrap(M), &buf_ptr, &buf_len);
        }
        if (buf_ptr && buf_len > 0) {
            // Assume the returned string was allocated
            // with LLVMPY_CreateByteString
            res = llvm::MemoryBuffer::getMemBufferCopy(
                llvm::StringRef(buf_ptr, buf_len));
            LLVMPY_DisposeString(buf_ptr);
        }
        return res;
    }

private:
    ObjectCacheNotifyFunc notify_func;
    ObjectCacheGetObjectFunc getobject_func;
};

typedef LLVMPYObjectCache *LLVMPYObjectCacheRef;


API_EXPORT(LLVMPYObjectCacheRef)
LLVMPY_CreateObjectCache(ObjectCacheNotifyFunc notify_func,
                         ObjectCacheGetObjectFunc getobject_func)
{
    return new LLVMPYObjectCache(notify_func, getobject_func);
}

API_EXPORT(void)
LLVMPY_DisposeObjectCache(LLVMPYObjectCacheRef C)
{
    delete C;
}

API_EXPORT(void)
LLVMPY_SetObjectCache(LLVMExecutionEngineRef EE, LLVMPYObjectCacheRef C)
{
    llvm::unwrap(EE)->setObjectCache(C);
}


} // end extern "C"
