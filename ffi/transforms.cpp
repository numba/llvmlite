#include "core.h"
#include "llvm-c/Transforms/PassManagerBuilder.h"
#include "llvm-c/Target.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Analysis/PostDominators.h"
#include "llvm/Analysis/DominanceFrontier.h"
#include "llvm/Analysis/RegionInfo.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/RegionPrinter.h"


#include <iostream>

extern "C" {

namespace llvm {
    inline PassManagerBuilder *unwrap(LLVMPassManagerBuilderRef P) {
        return reinterpret_cast<PassManagerBuilder*>(P);
    }

    inline LLVMPassManagerBuilderRef wrap(PassManagerBuilder *P) {
      return reinterpret_cast<LLVMPassManagerBuilderRef>(P);
    }

};

API_EXPORT(LLVMPassManagerBuilderRef)
LLVMPY_PassManagerBuilderCreate()
{
    return LLVMPassManagerBuilderCreate();
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderDispose(LLVMPassManagerBuilderRef PMB)
{
    LLVMPassManagerBuilderDispose(PMB);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateModulePassManager(
                            LLVMPassManagerBuilderRef PMB,
                            LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateModulePassManager(PMB, PM);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetOptLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->OptLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetOptLevel(LLVMPassManagerBuilderRef PMB,
                                  unsigned OptLevel)
{
    LLVMPassManagerBuilderSetOptLevel(PMB, OptLevel);
}

API_EXPORT(unsigned)
LLVMPY_PassManagerBuilderGetSizeLevel(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SizeLevel;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSizeLevel(LLVMPassManagerBuilderRef PMB,
                                   unsigned SizeLevel)
{
    LLVMPassManagerBuilderSetSizeLevel(PMB, SizeLevel);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnitAtATime;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnitAtATime(LLVMPassManagerBuilderRef PMB,
                                            int Value)
{
    LLVMPassManagerBuilderSetDisableUnitAtATime(PMB, Value);
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->DisableUnrollLoops;
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderSetDisableUnrollLoops(LLVMPassManagerBuilderRef PMB,
                                            LLVMBool Value)
{
    LLVMPassManagerBuilderSetDisableUnrollLoops(PMB, Value);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderUseInlinerWithThreshold(LLVMPassManagerBuilderRef PMB,
                                                 unsigned Threshold)
{
    LLVMPassManagerBuilderUseInlinerWithThreshold(PMB, Threshold);
}

API_EXPORT(void)
LLVMPY_PassManagerBuilderPopulateFunctionPassManager(
                                        LLVMPassManagerBuilderRef PMB,
                                        LLVMPassManagerRef PM)
{
    LLVMPassManagerBuilderPopulateFunctionPassManager(PMB, PM);
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetLoopVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->LoopVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetLoopVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->LoopVectorize;
}


API_EXPORT(void)
LLVMPY_PassManagerBuilderSetSLPVectorize(LLVMPassManagerBuilderRef PMB,
                                          int Value)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    pmb->SLPVectorize = Value;
}

API_EXPORT(int)
LLVMPY_PassManagerBuilderGetSLPVectorize(LLVMPassManagerBuilderRef PMB)
{
    llvm::PassManagerBuilder *pmb = llvm::unwrap(PMB);
    return pmb->SLPVectorize;
}


///////// Implement a FunctionPass to extract CFG Structures /////////

namespace {

using namespace llvm;


/// A simple pass that dumps several control-flow analysis passes
struct ControlStructuresDump : FunctionPass{
    static char ID;

    raw_ostream & out;

    ControlStructuresDump (raw_ostream & out)
        : FunctionPass(ID), out(out) { }

    bool runOnFunction(Function &F) {
        const Module *M = F.getParent();
        const char prefix[] = ">>> ";
        out << prefix << "regions\n";
        getAnalysis<RegionInfoPass>().print(out, M);
        out << prefix << "postdoms\n";
        getAnalysis<PostDominatorTree>().print(out, M);
        out << prefix << "domfront\n";
        getAnalysis<DominanceFrontier>().print(out, M);
        out << prefix << "doms\n";
        getAnalysis<DominatorTreeWrapperPass>().print(out, M);
        out << prefix << "loops\n";
        getAnalysis<LoopInfo>().print(out, M);

        return false;
    }

    void getAnalysisUsage(AnalysisUsage &AU) const {
        AU.setPreservesAll();
        AU.addRequired<RegionInfoPass>();
        AU.addRequired<PostDominatorTree>();
        AU.addRequired<DominanceFrontier>();
        AU.addRequired<DominatorTreeWrapperPass>();
        AU.addRequired<LoopInfo>();
    }

    const char * getPassName() const {
        return "llvmlite Control Structure Dump ";
    }

    static void AddPasses(FunctionPassManager &FPM, raw_ostream &out) {
        FPM.add(new LoopInfo());
        FPM.add(new RegionInfoPass());
        FPM.add(new ControlStructuresDump(out));
    }
};

char ControlStructuresDump ::ID = 0;

}

API_EXPORT(void)
LLVMPY_RunControlStructuresAnalysis(LLVMValueRef Fval, const char **Out)
{
    using namespace llvm;
    Function *F = unwrap<Function>(Fval);
    FunctionPassManager FPM(F->getParent());

    std::string buf;
    raw_string_ostream out(buf);

    ControlStructuresDump::AddPasses(FPM, out);

    FPM.doInitialization();
    FPM.run(*F);
    FPM.doFinalization();

    out.flush();

    *Out = LLVMPY_CreateString(out.str().c_str());
}


} // end extern "C"
