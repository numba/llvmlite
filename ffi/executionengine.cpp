#include "core.h"
#include "memorymanager.h"

#include "llvm-c/ExecutionEngine.h"
#include "llvm-c/Object.h"

#include "llvm/ExecutionEngine/ExecutionEngine.h"
#include "llvm/ExecutionEngine/JITEventListener.h"
#include "llvm/ExecutionEngine/ObjectCache.h"
#include "llvm/IR/Module.h"
#include "llvm/Object/Binary.h"
#include "llvm/Object/ObjectFile.h"
#include "llvm/Support/Memory.h"

#include <cstdio>
#include <memory>

namespace llvm {

// wrap/unwrap for LLVMTargetMachineRef.
// Ripped from lib/Target/TargetMachineC.cpp.

inline TargetMachine *unwrap(LLVMTargetMachineRef P) {
    return reinterpret_cast<TargetMachine *>(P);
}
inline LLVMTargetMachineRef wrap(const TargetMachine *P) {
    return reinterpret_cast<LLVMTargetMachineRef>(
        const_cast<TargetMachine *>(P));
}

// unwrap for LLVMObjectFileRef
// from Object/Object.cpp
namespace object {

inline OwningBinary<ObjectFile> *unwrap(LLVMObjectFileRef OF) {
    return reinterpret_cast<OwningBinary<ObjectFile> *>(OF);
}
} // namespace object
} // namespace llvm

extern "C" {

API_EXPORT(void)
LLVMPY_LinkInMCJIT() { LLVMLinkInMCJIT(); }

API_EXPORT(void)
LLVMPY_DisposeExecutionEngine(LLVMExecutionEngineRef EE) {
    LLVMDisposeExecutionEngine(EE);
}

API_EXPORT(void)
LLVMPY_AddModule(LLVMExecutionEngineRef EE, LLVMModuleRef M) {
    LLVMAddModule(EE, M);
}

API_EXPORT(int)
LLVMPY_RemoveModule(LLVMExecutionEngineRef EE, LLVMModuleRef M,
                    char **OutError) {
    return LLVMRemoveModule(EE, M, &M, OutError);
}

API_EXPORT(void)
LLVMPY_FinalizeObject(LLVMExecutionEngineRef EE) {
    llvm::unwrap(EE)->finalizeObject();
}

static LLVMExecutionEngineRef create_execution_engine(LLVMModuleRef M,
                                                      LLVMTargetMachineRef TM,
                                                      bool use_lmm,
                                                      const char **OutError) {
    LLVMExecutionEngineRef ee = nullptr;

    llvm::EngineBuilder eb(std::unique_ptr<llvm::Module>(llvm::unwrap(M)));
    std::string err;
    eb.setErrorStr(&err);
    eb.setEngineKind(llvm::EngineKind::JIT);

    if (use_lmm) {
        std::unique_ptr<llvm::RTDyldMemoryManager> mm =
            std::make_unique<llvm::LlvmliteMemoryManager>();
        eb.setMCJITMemoryManager(std::move(mm));
    }

    /* EngineBuilder::create loads the current process symbols */
    llvm::ExecutionEngine *engine = eb.create(llvm::unwrap(TM));

    if (!engine)
        *OutError = LLVMPY_CreateString(err.c_str());
    else
        ee = llvm::wrap(engine);
    return ee;
}

API_EXPORT(LLVMExecutionEngineRef)
LLVMPY_CreateMCJITCompiler(LLVMModuleRef M, LLVMTargetMachineRef TM,
                           bool use_lmm, const char **OutError) {
    return create_execution_engine(M, TM, use_lmm, OutError);
}

API_EXPORT(uint64_t)
LLVMPY_GetGlobalValueAddress(LLVMExecutionEngineRef EE, const char *Name) {
    return LLVMGetGlobalValueAddress(EE, Name);
}

API_EXPORT(uint64_t)
LLVMPY_GetFunctionAddress(LLVMExecutionEngineRef EE, const char *Name) {
    return LLVMGetFunctionAddress(EE, Name);
}

API_EXPORT(void)
LLVMPY_RunStaticConstructors(LLVMExecutionEngineRef EE) {
    return LLVMRunStaticConstructors(EE);
}

API_EXPORT(void)
LLVMPY_RunStaticDestructors(LLVMExecutionEngineRef EE) {
    return LLVMRunStaticDestructors(EE);
}

API_EXPORT(void)
LLVMPY_AddGlobalMapping(LLVMExecutionEngineRef EE, LLVMValueRef Global,
                        void *Addr) {
    LLVMAddGlobalMapping(EE, Global, Addr);
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_GetExecutionEngineTargetData(LLVMExecutionEngineRef EE) {
    return LLVMGetExecutionEngineTargetData(EE);
}

API_EXPORT(int)
LLVMPY_TryAllocateExecutableMemory(void) {
    using namespace llvm::sys;
    std::error_code ec;
    MemoryBlock mb = Memory::allocateMappedMemory(
        4096, nullptr, Memory::MF_READ | Memory::MF_WRITE, ec);
    if (!ec) {
        ec = Memory::protectMappedMemory(mb, Memory::MF_READ | Memory::MF_EXEC);
        (void)Memory::releaseMappedMemory(mb); /* Should always succeed */
    }
    return ec.value();
}

API_EXPORT(bool)
LLVMPY_EnableJITEvents(LLVMExecutionEngineRef EE) {
    llvm::JITEventListener *listener;
    bool result = false;

#ifdef __linux__
    listener = llvm::JITEventListener::createOProfileJITEventListener();
    // if listener is null, then LLVM was not compiled for OProfile JIT events.
    if (listener) {
        llvm::unwrap(EE)->RegisterJITEventListener(listener);
        result = true;
    }
#endif
    listener = llvm::JITEventListener::createIntelJITEventListener();
    // if listener is null, then LLVM was not compiled for Intel JIT events.
    if (listener) {
        llvm::unwrap(EE)->RegisterJITEventListener(listener);
        result = true;
    }
    return result;
}

API_EXPORT(void)
LLVMPY_MCJITAddObjectFile(LLVMExecutionEngineRef EE, LLVMObjectFileRef ObjF) {
    using namespace llvm;
    using namespace llvm::object;
    auto engine = unwrap(EE);
    auto object_file = unwrap(ObjF);
    auto binary_tuple = object_file->takeBinary();

    engine->addObjectFile(
        {std::move(binary_tuple.first), std::move(binary_tuple.second)});
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
                      ObjectCacheGetObjectFunc getobject_func, void *user_data)
        : notify_func(notify_func), getobject_func(getobject_func),
          user_data(user_data) {}

    virtual void notifyObjectCompiled(const llvm::Module *M,
                                      llvm::MemoryBufferRef MBR) {
        if (notify_func) {
            ObjectCacheData data = {llvm::wrap(M), MBR.getBufferStart(),
                                    MBR.getBufferSize()};
            notify_func(user_data, &data);
        }
    }

    // MCJIT will call this function before compiling any module
    // MCJIT takes ownership of both the MemoryBuffer object and the memory
    // to which it refers.
    virtual std::unique_ptr<llvm::MemoryBuffer>
    getObject(const llvm::Module *M) {
        std::unique_ptr<llvm::MemoryBuffer> res = nullptr;

        if (getobject_func) {
            ObjectCacheData data = {llvm::wrap(M), nullptr, 0};

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
                         void *user_data) {
    return new LLVMPYObjectCache(notify_func, getobject_func, user_data);
}

API_EXPORT(void)
LLVMPY_DisposeObjectCache(LLVMPYObjectCacheRef C) { delete C; }

API_EXPORT(void)
LLVMPY_SetObjectCache(LLVMExecutionEngineRef EE, LLVMPYObjectCacheRef C) {
    llvm::unwrap(EE)->setObjectCache(C);
}

} // end extern "C"
