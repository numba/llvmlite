#pragma once
#include "llvm/Analysis/CGSCCPassManager.h"
#include "llvm/Analysis/LoopAnalysisManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Pass.h"
#include "llvm/Passes/OptimizationLevel.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Target/TargetMachine.h"

namespace llvmlite {

struct BridgedPassManagerCallbacks {
    char *(*process_module)(void *context, const char *llvm_ir,
                            size_t llvm_ir_len, size_t *output_ir_len);
    void (*dtor)(void *);
    void *(*ctor)();
};

typedef llvm::OptimizationLevel
ModulePassManagerInitializer(llvm::PassBuilder &pass_builder);

/**
 * Bridge pass managers are a way to add passes from an LLVM that was not linked
 * with llvmlite.
 *
 * The nature of C++'s templates makes generating a C++ shared library hard at
 * the best of times and the LLVM library is sufficiently weird and complicated
 * that delivering it as a shared library has lots of drawbacks, regardless of
 * how much Debian packging tries. It certainly makes it impossible to load two
 * different version of LLVM into the same process, say when Numba and Julia
 * want to collaborate. To make this work, llvmlite's policy is to statically
 * link against LLVM and strip all symbols, giving it essentially a private copy
 * of LLVM. Unfortunately, this means that any passes need to be compiled into
 * llvmlite since they have no way to access the necessary symbols.
 *
 * This code allows creating a "bridge" between two LLVM compilers by exchanging
 * only IR. The host LLVM instance, compiled into llvmlite, will run a pass
 * which converts a module to IR and sends it via a C ABI to another "guest"
 * pass manager which parses the IR, runs various passes on it, and converts it
 * back to text where it is returned to the host, which can then parse it and
 * merge the changes into the original module and allow the "host" LLVM compiler
 * to continue to operate it.
 *
 * To use this interface, create a function with the signature of
 * `ModulePassManagerInitializer` that sets up the pass manager as you please.
 * No analysis passes will have been performed as the serialization process
 * necessarily destroys analysis information. Then, create a global symbol using
 * this template as follows: `llvmlite::BridgedPassManagerCallbacks my_callbacks
 * = llvmlite::BridgedPassGuest<my_pass_man_init_func>::bridge();`. Then, create
 * a Python binding that exposes `&my_callbacks` to Python. That can then be
 * added, in Python, using `PassManager.add_bridged_pass`. tada.wav
 *
 * This template will handle all of the LLVM initialization. You could create
 * more creative uses by directly implementing the `BridgedPassManagerCallbacks`
 * interface directly and do things like spin up a separate process or send
 * requests to a remote server. Get all Jurassic Park and ask if you can, not if
 * you should.
 *
 */
template <ModulePassManagerInitializer init> class BridgedPassGuest {
    llvm::LoopAnalysisManager loop_analysis_manager;
    llvm::FunctionAnalysisManager function_analysis_manager;
    llvm::CGSCCAnalysisManager cgscc_analysis_manager;
    llvm::ModuleAnalysisManager module_analysis_manager;
    llvm::ModulePassManager manager;

  public:
    BridgedPassGuest()
        : loop_analysis_manager(), function_analysis_manager(),
          cgscc_analysis_manager(), module_analysis_manager(),

          manager(prepare_manager(
              loop_analysis_manager, function_analysis_manager,
              cgscc_analysis_manager, module_analysis_manager)) {}

  private:
    static void *construct_instance() { return new BridgedPassGuest(); }
    static void destroy_instance(void *context) {
        delete static_cast<BridgedPassGuest *>(context);
    }
    static char *process_instance(void *context, const char *llvm_ir,
                                  size_t llvm_ir_len, size_t *output_ir_len) {
        return static_cast<BridgedPassGuest *>(context)->process_module(
            llvm_ir, llvm_ir_len, output_ir_len);
    }

    static llvm::ModulePassManager
    prepare_manager(llvm::LoopAnalysisManager &loop_analysis_manager,
                    llvm::FunctionAnalysisManager &function_analysis_manager,
                    llvm::CGSCCAnalysisManager &cgscc_analysis_manager,
                    llvm::ModuleAnalysisManager &module_analysis_manager) {
        llvm::PassBuilder pass_builder(nullptr);

        pass_builder.registerModuleAnalyses(module_analysis_manager);
        pass_builder.registerCGSCCAnalyses(cgscc_analysis_manager);
        pass_builder.registerFunctionAnalyses(function_analysis_manager);
        pass_builder.registerLoopAnalyses(loop_analysis_manager);
        pass_builder.crossRegisterProxies(
            loop_analysis_manager, function_analysis_manager,
            cgscc_analysis_manager, module_analysis_manager);

        auto optimization_level = init(pass_builder);

        return pass_builder.buildPerModuleDefaultPipeline(optimization_level);
    }
    char *process_module(const char *llvm_ir, size_t llvm_ir_len,
                         size_t *output_ir_len) {
        using namespace llvm;
        LLVMContext ctxt;
        SMDiagnostic error;
        auto module =
            parseIR(*MemoryBuffer::getMemBuffer(StringRef(llvm_ir, llvm_ir_len),
                                                "bridge-guest-rx", false),
                    error, ctxt);
        if (!module) {
            *output_ir_len = 0;
            return nullptr;
        }
        this->manager.run(*module, this->module_analysis_manager);
        std::string buf;
        raw_string_ostream os(buf);

        module->print(os, nullptr);
        os.flush();
        *output_ir_len = buf.length();
        return strdup(buf.c_str());
    }

  public:
    constexpr static BridgedPassManagerCallbacks bridge() {
        return {.process_module = &process_instance,
                .dtor = &destroy_instance,
                .ctor = &construct_instance};
    }
};
} // namespace llvmlite
