
#include "core.h"


#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"

#include "llvm/ADT/SmallString.h"
#include "llvm/ADT/SetVector.h"

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
#include <map>

using namespace llvm;

namespace llvm {
    void initializeRefPrunePassPass(PassRegistry &Registry);
}

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
    SmallVector<CallInst*, 20> incref_list, decref_list;
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
    mutated |= eraseNullFirstArgFromList(incref_list);
    mutated |= eraseNullFirstArgFromList(decref_list);

    // Check pairs that are dominating and postdominating each other
    for (CallInst*& incref: incref_list) {
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
                incref = NULL;
                decref = NULL;
                mutated |= true;
                break;
            }
        }
    }

    // Deal with fanout
    // a single incref with multiple decrefs in outgoing edges
    for (CallInst*& incref : incref_list) {
        if (incref == NULL) continue;

        Instruction* term = incref->getParent()->getTerminator();
        if (term->getNumSuccessors() > 0) {
            errs() << "======= AT\n" ;
            SetVector<CallInst*> candidates;
            incref->dump();
            bool balanced = true;
            for (unsigned int i = 0; i < term->getNumSuccessors(); ++i) {
                DomTreeNode* domchild = domtree.getNode(term->getSuccessor(i));

                errs() << "==== check " << domchild->getBlock()->getName() << "\n";
                if (!findDecrefDominatedByNode(domtree, postdomtree, domchild, incref,
                                            candidates)) {
                    balanced = false;
                }
            }
            if (balanced) {
                errs() << "======balanced" << "\n";
                for (CallInst* inst : candidates)  {
                    inst->dump();
                }
                errs() << "======" << "\n";
                incref->eraseFromParent();
                for (CallInst* inst : candidates)  {
                    inst->eraseFromParent();
                }
                incref = NULL;
                mutated |= true;
            }
        }
    }
    return mutated;
  }

  template <class T>
  bool eraseNullFirstArgFromList(T& refops) {
    bool mutated = false;
    for (CallInst*& refop: refops) {
        if (!isNonNullFirstArg(refop)) {
            refop->eraseFromParent();
            mutated |= true;
            refop = NULL;
        }
    }
    return mutated;
  }

  bool findDecrefDominatedByNode(DominatorTree &domtree,
                               PostDominatorTree &postdomtree,
                               DomTreeNode* dom_root,
                               CallInst* incref,
                               SetVector<CallInst*> &candidates,
                               unsigned int depth=0) {

    bool found = false;
    BasicBlock* bb_root = dom_root->getBlock();

    errs() << "   -- findDecrefDominatedByNode: " << bb_root->getName() << "\n";

    for (CallInst *decref : findRelatedDecrefs(dom_root->getBlock(), incref) ){
        if ( domtree.dominates(incref, decref) ){
            errs() << "   found\n";
            decref->dump();

            candidates.insert(decref);
            found = true;
            // stop on first result
            break;
        }
    }

    if (found) return true;

    if (depth > 10) {
        return false;
    }

    for (DomTreeNode* dom_child : dom_root->getChildren()) {
        if (!findDecrefDominatedByNode(domtree, postdomtree, dom_child, incref, candidates, depth + 1)) {
            return false;
        }
    }
    return true;
  }

  /**
   * Find related decrefs to incref inside a basicblock in order
   */
  std::vector<CallInst*> findRelatedDecrefs(BasicBlock* bb, CallInst* incref) {
      std::vector<CallInst*> res;
      for (Instruction &ii : *bb) {
        if (ii.getOpcode() == Instruction::Call) {
            CallInst *call_inst = dyn_cast<CallInst>(&ii);
            Value *callee = call_inst->getCalledOperand();
            if ( callee->getName() != "NRT_decref" ) {
                continue;
            }
            if (incref->getArgOperand(0) != call_inst->getArgOperand(0)) {
                continue;
            }
            res.push_back(call_inst);
        }
      }
      return res;
  }

   void getAnalysisUsage(AnalysisUsage &Info) const override {
       Info.addRequired<DominatorTreeWrapperPass>();
       Info.addRequired<PostDominatorTreeWrapperPass>();
   }

   bool isNonNullFirstArg(CallInst *call_inst){
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