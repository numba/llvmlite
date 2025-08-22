#include "core.h"
#include "llvm-c/LLJIT.h"
#include "llvm-c/Orc.h"
#include <sstream>

#include "llvm/AsmParser/Parser.h"
#include "llvm/ExecutionEngine/Orc/Core.h"
#include "llvm/ExecutionEngine/Orc/Debugging/DebuggerSupportPlugin.h"
#include "llvm/ExecutionEngine/Orc/ExecutionUtils.h"
#include "llvm/ExecutionEngine/Orc/LLJIT.h"
#include "llvm/ExecutionEngine/Orc/ObjectLinkingLayer.h"
#include "llvm/ExecutionEngine/Orc/RTDyldObjectLinkingLayer.h"
#include "llvm/ExecutionEngine/SectionMemoryManager.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SourceMgr.h"

using namespace llvm;
using namespace llvm::orc;

inline LLJIT *unwrap(LLVMOrcLLJITRef P) { return reinterpret_cast<LLJIT *>(P); }

inline TargetMachine *unwrap(LLVMTargetMachineRef TM) {
    return reinterpret_cast<TargetMachine *>(TM);
}

inline LLVMOrcJITTargetMachineBuilderRef wrap(JITTargetMachineBuilder *JTMB) {
    return reinterpret_cast<LLVMOrcJITTargetMachineBuilderRef>(JTMB);
}

static void destroyError(Error e) {
    /* LLVM's Error type will abort if you don't read it. */
    LLVMDisposeErrorMessage(LLVMGetErrorMessage(wrap(std::move(e))));
}

class JITDylibTracker {
  public:
    std::shared_ptr<LLJIT> lljit;
    JITDylib &dylib;
    IntrusiveRefCntPtr<llvm::orc::ResourceTracker> tracker;
    JITDylibTracker(std::shared_ptr<LLJIT> &lljit_, JITDylib &dylib_,
                    IntrusiveRefCntPtr<llvm::orc::ResourceTracker> &&tracker_)
        : lljit(lljit_), dylib(dylib_), tracker(tracker_) {}
};

typedef struct {
    uint8_t element_kind;
    char *value;
    size_t value_len;
} LinkElement;
typedef struct {
    char *name;
    uint64_t address;
} SymbolAddress;
extern "C" {

API_EXPORT(std::shared_ptr<LLJIT> *)
LLVMPY_CreateLLJITCompiler(LLVMTargetMachineRef tm, bool suppressErrors,
                           bool useJitLink, const char **OutError) {
    LLJITBuilder builder;
#ifdef _WIN32
    if (useJitLink) {
        *OutError = LLVMPY_CreateString(
            "JITLink is not currently available on Windows");
        return nullptr;
    }
#endif
    if (tm) {
        // The following is based on
        // LLVMOrcJITTargetMachineBuilderCreateFromTargetMachine. However,
        // we can't use that directly because it destroys the target
        // machine, but we need to keep it alive because it is referenced by
        // / shared with other objects on the Python side.
        auto *template_tm = unwrap(tm);

        builder.setJITTargetMachineBuilder(
            JITTargetMachineBuilder(template_tm->getTargetTriple())
                .setCPU(template_tm->getTargetCPU().str())
                .setRelocationModel(template_tm->getRelocationModel())
                .setCodeModel(template_tm->getCodeModel())
                .setCodeGenOptLevel(template_tm->getOptLevel())
                .setFeatures(template_tm->getTargetFeatureString())
                .setOptions(template_tm->Options));
    }
    builder.setObjectLinkingLayerCreator(
        [=](llvm::orc::ExecutionSession &session, const llvm::Triple &triple)
            -> std::unique_ptr<llvm::orc::ObjectLayer> {
            if (useJitLink) {
                auto linkingLayer =
                    std::make_unique<llvm::orc::ObjectLinkingLayer>(session);

                /* FIXME(LLVM16): In newer LLVM versions, there is a simple
                 * EnableDebugSupport flag on the builder and we don't need to
                 * do any of this. */
                //  if (triple.getObjectFormat() == Triple::ELF ||
                //     triple.getObjectFormat() == Triple::MachO) {
                //     linkingLayer->addPlugin(
                //         std::make_unique<orc::GDBJITDebugInfoRegistrationPlugin>(
                //             ExecutorAddr::fromPtr(
                //                 &llvm_orc_registerJITLoaderGDBWrapper)));
                // }
                if (triple.isOSBinFormatCOFF()) {
                    linkingLayer->setOverrideObjectFlagsWithResponsibilityFlags(
                        true);
                    linkingLayer->setAutoClaimResponsibilityForObjectSymbols(
                        true);
                }
                return linkingLayer;
            } else {
                auto linkingLayer = std::make_unique<
                    llvm::orc::RTDyldObjectLinkingLayer>(session, []() {
                    return std::make_unique<llvm::SectionMemoryManager>();
                });
                if (triple.isOSBinFormatCOFF()) {
                    linkingLayer->setOverrideObjectFlagsWithResponsibilityFlags(
                        true);
                    linkingLayer->setAutoClaimResponsibilityForObjectSymbols(
                        true);
                }
                linkingLayer->registerJITEventListener(
                    *llvm::JITEventListener::createGDBRegistrationListener());

                return linkingLayer;
            }
        });

    auto jit = builder.create();

    if (!jit) {
        char *message = LLVMGetErrorMessage(wrap(jit.takeError()));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);
        return nullptr;
    }
    if (suppressErrors) {
        (*jit)->getExecutionSession().setErrorReporter(destroyError);
    }
    return new std::shared_ptr<LLJIT>(std::move(*jit));
}

API_EXPORT(JITDylibTracker *)
LLVMPY_LLJITLookup(std::shared_ptr<LLJIT> *lljit, const char *dylib_name,
                   const char *name, uint64_t *addr, const char **OutError) {

    auto dylib = (*lljit)->getJITDylibByName(dylib_name);
    if (!dylib) {
        *OutError = LLVMPY_CreateString("No such library");
        return nullptr;
    }

    auto sym = (*lljit)->lookup(*dylib, name);
    if (!sym) {
        char *message = LLVMGetErrorMessage(wrap(sym.takeError()));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);
        return nullptr;
    }

    *addr = sym->getValue();
    return new JITDylibTracker(*lljit, *dylib,
                               std::move(dylib->createResourceTracker()));
}

API_EXPORT(LLVMTargetDataRef)
LLVMPY_LLJITGetDataLayout(std::shared_ptr<LLJIT> *lljit) {
    return wrap(&(*lljit)->getDataLayout());
}

API_EXPORT(void)
LLVMPY_LLJITDispose(std::shared_ptr<LLJIT> *lljit) { delete lljit; }

API_EXPORT(JITDylibTracker *)
LLVMPY_LLJIT_Link(std::shared_ptr<LLJIT> *lljit, const char *libraryName,
                  LinkElement *elements, size_t elements_length,
                  SymbolAddress *imports, size_t imports_length,
                  SymbolAddress *exports, size_t exports_length,
                  const char **OutError) {
    if ((*lljit)->getJITDylibByName(libraryName) != nullptr) {
        std::stringstream err;
        err << "Library name `" << libraryName << "' is already in use.";
        *OutError = LLVMPY_CreateString(err.str().c_str());
        return nullptr;
    }
    auto dylib = (*lljit)->createJITDylib(libraryName);

    if (!dylib) {
        char *message = LLVMGetErrorMessage(wrap(std::move(dylib.takeError())));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);
        return nullptr;
    }

    for (size_t import_idx = 0; import_idx < imports_length; import_idx++) {
        SymbolStringPtr mangled =
            (*lljit)->mangleAndIntern(imports[import_idx].name);
        ExecutorSymbolDef symbol(ExecutorAddr(imports[import_idx].address),
                                 JITSymbolFlags::Exported);

        auto error = dylib->define(absoluteSymbols({{mangled, symbol}}));

        if (error) {
            char *message = LLVMGetErrorMessage(wrap(std::move(error)));
            *OutError = LLVMPY_CreateString(message);
            LLVMDisposeErrorMessage(message);
            return nullptr;
        }
    }

    for (size_t element_idx = 0; element_idx < elements_length; element_idx++) {
        switch (elements[element_idx].element_kind) {
        case 0: // Adding IR
        {
            auto ctxt = std::make_unique<LLVMContext>();
            SMDiagnostic error;
            auto module =
                parseIR(*MemoryBuffer::getMemBuffer(
                            StringRef(elements[element_idx].value,
                                      elements[element_idx].value_len),
                            "ir", false),
                        error, *ctxt);
            if (!module) {
                std::string osbuf;
                raw_string_ostream os(osbuf);
                error.print("", os);
                os.flush();
                *OutError = LLVMPY_CreateString(os.str().c_str());
                return nullptr;
            }
            auto addError = (*lljit)->addIRModule(
                *dylib, ThreadSafeModule(std::move(module), std::move(ctxt)));
            if (addError) {
                char *message = LLVMGetErrorMessage(wrap(std::move(addError)));
                *OutError = LLVMPY_CreateString(message);
                LLVMDisposeErrorMessage(message);
                return nullptr;
            }
        }; break;
        case 1: // Adding native assembly
        {
            auto ctxt = std::make_unique<LLVMContext>();
            SMDiagnostic error;
            auto module =
                parseAssembly(*MemoryBuffer::getMemBuffer(
                                  StringRef(elements[element_idx].value,
                                            elements[element_idx].value_len),
                                  "asm", false),
                              error,

                              *ctxt);
            if (!module) {
                std::string osbuf;
                raw_string_ostream os(osbuf);
                error.print("", os);
                os.flush();
                *OutError = LLVMPY_CreateString(os.str().c_str());
                return nullptr;
            }
            auto addError = (*lljit)->addIRModule(
                *dylib, ThreadSafeModule(std::move(module), std::move(ctxt)));
            if (addError) {
                char *message = LLVMGetErrorMessage(wrap(std::move(addError)));
                *OutError = LLVMPY_CreateString(message);
                LLVMDisposeErrorMessage(message);
                return nullptr;
            }
        }; break;
        case 2: // Adding object code
        {
            auto addError = (*lljit)->addObjectFile(
                *dylib, MemoryBuffer::getMemBufferCopy(
                            StringRef(elements[element_idx].value,
                                      elements[element_idx].value_len)));
            if (addError) {
                char *message = LLVMGetErrorMessage(wrap(std::move(addError)));
                *OutError = LLVMPY_CreateString(message);
                LLVMDisposeErrorMessage(message);
                return nullptr;
            }
        }; break;
        case 3: // Adding existing library
            // Take an empty name to be the current process
            if (elements[element_idx].value_len) {
                auto other = (*lljit)->getJITDylibByName(
                    StringRef(elements[element_idx].value,
                              elements[element_idx].value_len));
                if (!other) {
                    std::string osbuf;
                    raw_string_ostream os(osbuf);
                    os << "Failed to find library `"
                       << StringRef(elements[element_idx].value,
                                    elements[element_idx].value_len)
                       << "'.";
                    os.flush();
                    *OutError = LLVMPY_CreateString(osbuf.c_str());
                    return nullptr;
                }
                dylib->addToLinkOrder(*other);
            } else {
                auto prefix = (*lljit)->getDataLayout().getGlobalPrefix();
                auto DLSGOrErr =
                    DynamicLibrarySearchGenerator::GetForCurrentProcess(prefix);
                if (DLSGOrErr) {
                    dylib->addGenerator(std::move(*DLSGOrErr));
                } else {
                    char *message =
                        LLVMGetErrorMessage(wrap(DLSGOrErr.takeError()));
                    *OutError = LLVMPY_CreateString(message);
                    LLVMDisposeErrorMessage(message);
                    return nullptr;
                }
            }
            break;

        default:
            *OutError = LLVMPY_CreateString("Unknown element type");
            return nullptr;
        }
    }
    auto initError = (*lljit)->initialize(*dylib);
    if (initError) {
        char *message = LLVMGetErrorMessage(wrap(std::move(initError)));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);

        return nullptr;
    }
    for (size_t export_idx = 0; export_idx < exports_length; export_idx++) {
        auto lookup = (*lljit)->lookup(*dylib, exports[export_idx].name);
        if (!lookup) {
            char *message =
                LLVMGetErrorMessage(wrap(std::move(lookup.takeError())));
            *OutError = LLVMPY_CreateString(message);
            LLVMDisposeErrorMessage(message);
            return nullptr;
        }
        exports[export_idx].address = lookup->getValue();
    }
    return new JITDylibTracker(*lljit, *dylib,
                               std::move(dylib->getDefaultResourceTracker()));
}

API_EXPORT(bool)
LLVMPY_LLJIT_Dylib_Tracker_Dispose(JITDylibTracker *tracker,
                                   const char **OutError) {
    *OutError = nullptr;
    auto result = false;
    /* This is undoubtedly a really bad and fragile check. LLVM creates a bunch
     * of platform support to know if there's deinitializers to run. If we try
     * to run them when they aren't present, a bunch of junk will be printed to
     * stderr. So, we're rummaging around for an internal symbol in its platform
     * support library and skipping the deinitialization if we don't find. */
    auto lookup = tracker->lljit->lookup(tracker->dylib,
                                         "__lljit.platform_support_instance");
    if (lookup) {
        auto error = tracker->lljit->deinitialize(tracker->dylib);
        if (error) {
            char *message = LLVMGetErrorMessage(wrap(std::move(error)));
            *OutError = LLVMPY_CreateString(message);
            LLVMDisposeErrorMessage(message);
            result = true;
        }
    } else {
        destroyError(std::move(lookup.takeError()));
    }
    auto error = tracker->dylib.clear();
    if (error && !result) {
        char *message = LLVMGetErrorMessage(wrap(std::move(error)));
        *OutError = LLVMPY_CreateString(message);
        LLVMDisposeErrorMessage(message);
        result = true;
    }
    delete tracker;

    return result;
}

} // extern "C"
