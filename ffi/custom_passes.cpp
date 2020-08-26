
#include "core.h"


#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Analysis/Passes.h"
#include "llvm/Analysis/RegionPass.h"
#include "llvm/Analysis/RegionInfo.h"
#include "llvm/Analysis/RegionPrinter.h"
#include "llvm/Analysis/PostDominators.h"
#include "llvm/Analysis/DomPrinter.h"
#include "llvm/Transforms/Utils/UnifyFunctionExitNodes.h"

#include "llvm/Transforms/Scalar.h"

#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

#include "llvm/InitializePasses.h"
#include "llvm/LinkAllPasses.h"

#include <vector>

using namespace llvm;

namespace llvm {
    void initializeRefPrunePassPass(PassRegistry &Registry);
}
/*
struct Hello : public RegionPass {
  static char ID;
  Hello() : RegionPass(ID) {
      initializeHelloPass(*PassRegistry::getPassRegistry());
  }

  bool runOnRegion(Region *region, RGPassManager &RGM) override {
    errs() << "Hello: ";
    errs().write_escaped(region->getNameStr()) << '\n';
    return false;
  }
}; // end of struct Hello
*/


struct RefPrunePass : public FunctionPass {
  static char ID;
  RefPrunePass() : FunctionPass(ID) {
      initializeRefPrunePassPass(*PassRegistry::getPassRegistry());
  }

  bool runOnFunction(Function &F) override {
    errs() << "NRT_RefPrunePass\n";
    errs().write_escaped(F.getName()) << '\n';

    auto &domtree = getAnalysis<DominatorTreeWrapperPass>().getDomTree();
    auto &postdomtree = getAnalysis<PostDominatorTreeWrapperPass>().getPostDomTree();

    // domtree.viewGraph();   // view domtree
    // postdomtree.viewGraph();

    bool mutated = false;

    // Find all incref & decref
    std::vector<CallInst*> incref_list, decref_list;
    for (BasicBlock &bb : F) {
        for (Instruction &ii : bb) {
            if (ii.getOpcode() == Instruction::Call) {
                CallInst *call_inst = dyn_cast<CallInst>(&ii);
                // TODO: handle call_inst being NULL
                Value *callee = call_inst->getCalledOperand();
                if ( callee->getName() == "NRT_incref" ) {
                    incref_list.push_back(call_inst);
                } else if ( callee->getName() == "NRT_decref" ) {
                    decref_list.push_back(call_inst);
                }
            }
        }
    }

    errs() << "Counts " << incref_list.size() << " " << decref_list.size() << "\n";

    // Drop refops on NULL pointers
    for (CallInst*& refop: incref_list) {
        if (!keepNonNullArg(refop)) {
            refop->eraseFromParent();
            mutated |= true;
            refop = NULL;
        }
    }
    for (CallInst*& refop: decref_list) {
        if (!keepNonNullArg(refop)) {
            refop->eraseFromParent();
            mutated |= true;
            refop = NULL;
        }
    }

    // check pairs that are dominating and postdominating each other
    for (CallInst* incref: incref_list) {
        if (incref == NULL) continue;

        for (CallInst*& decref: decref_list) {
            if (decref == NULL) continue;

            if (incref->getArgOperand(0) != decref->getArgOperand(0) )
                continue;

            if ( domtree.dominates(incref, decref)
                    && postdomtree.dominates(decref, incref) ){
                errs() << "Prune these due to DOM + PDOM\n";
                incref->dump();
                decref->dump();
                errs() << "\n";
                incref->eraseFromParent();
                decref->eraseFromParent();
                decref = NULL;
                mutated |= true;
                continue;
            }
        }
    }
    return mutated;
  }

   void getAnalysisUsage(AnalysisUsage &Info) const override {
       Info.addRequired<DominatorTreeWrapperPass>();
       Info.addRequired<PostDominatorTreeWrapperPass>();
   }

   bool keepNonNullArg(CallInst *call_inst){
       auto val = call_inst->getArgOperand(0);
       auto ptr = dyn_cast<ConstantPointerNull>(val);
       return ptr == NULL;
   }
}; // end of struct RefPrunePass


char RefPrunePass::ID = 0;

INITIALIZE_PASS_BEGIN(RefPrunePass, "nrtrefprunepass",
                      "Prune NRT refops", false, false)
// INITIALIZE_PASS_DEPENDENCY(RegionInfoPass)
INITIALIZE_PASS_DEPENDENCY(DominatorTreeWrapperPass)
INITIALIZE_PASS_DEPENDENCY(PostDominatorTreeWrapperPass)

INITIALIZE_PASS_END(RefPrunePass, "refprunepass",
                    "Prune NRT refops", false, false)


extern "C" {

API_EXPORT(void)
LLVMPY_AddRefPrunePass(LLVMPassManagerRef PM)
{
    // unwrap(PM)->add(createStructurizeCFGPass());
    // unwrap(PM)->add(createUnifyFunctionExitNodesPass());
    // unwrap(PM)->add(createPromoteMemoryToRegisterPass());
    // unwrap(PM)->add(createInstSimplifyLegacyPass());
    unwrap(PM)->add(new RefPrunePass());
}


} // extern "C"