#include "core.h"

#include "llvm-c/ExecutionEngine.h"

#include "llvm/IR/Module.h"
#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include "llvm/ExecutionEngine/JITEventListener.h"
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

API_EXPORT(bool)
LLVMPY_EnableJITEvents(LLVMExecutionEngineRef EE)
{
#ifdef __linux__
    llvm::JITEventListener *listener = llvm::JITEventListener::createOProfileJITEventListener();
    // if listener is null, then LLVM was not compiled for OProfile JIT events.
    if (listener) {
        llvm::unwrap(EE)->RegisterJITEventListener(listener);
        return true;
    }
#endif
    return false;
}


//
// Object cache
//

typedef struct {
    LLVMModuleRef modref;
    const char *buf_ptr;
    size_t buf_len;
} ObjectCacheData;

typedef void (*ObjectCacheNotifyFunc)(void *, const ObjectCacheData *);
typedef void (*ObjectCacheGetObjectFunc)(void *, ObjectCacheData *);


class LLVMPYObjectCache : public llvm::ObjectCache {
public:
    LLVMPYObjectCache(ObjectCacheNotifyFunc notify_func,
                      ObjectCacheGetObjectFunc getobject_func,
                      void *user_data)
    : notify_func(notify_func), getobject_func(getobject_func),
      user_data(user_data)
    {
    }

    virtual void notifyObjectCompiled(const llvm::Module *M,
                                      llvm::MemoryBufferRef MBR)
    {
        if (notify_func) {
            ObjectCacheData data = { llvm::wrap(M),
                                     MBR.getBufferStart(),
                                     MBR.getBufferSize() };
            notify_func(user_data, &data);
        }
    }

    // MCJIT will call this function before compiling any module
    // MCJIT takes ownership of both the MemoryBuffer object and the memory
    // to which it refers.
    virtual std::unique_ptr<llvm::MemoryBuffer> getObject(const llvm::Module* M)
    {
        std::unique_ptr<llvm::MemoryBuffer> res = nullptr;

        if (getobject_func) {
            ObjectCacheData data = { llvm::wrap(M), nullptr, 0 };

            getobject_func(user_data, &data);
            if (data.buf_ptr && data.buf_len > 0) {
                // Assume the returned string was allocated
                // with LLVMPY_CreateByteString
                res = llvm::MemoryBuffer::getMemBufferCopy(
                    llvm::StringRef(data.buf_ptr, data.buf_len));
                LLVMPY_DisposeString(data.buf_ptr);
            }
        }
        return res;
    }

private:
    ObjectCacheNotifyFunc notify_func;
    ObjectCacheGetObjectFunc getobject_func;
    void *user_data;
};

typedef LLVMPYObjectCache *LLVMPYObjectCacheRef;


API_EXPORT(LLVMPYObjectCacheRef)
LLVMPY_CreateObjectCache(ObjectCacheNotifyFunc notify_func,
                         ObjectCacheGetObjectFunc getobject_func,
                         void *user_data)
{
    return new LLVMPYObjectCache(notify_func, getobject_func, user_data);
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
