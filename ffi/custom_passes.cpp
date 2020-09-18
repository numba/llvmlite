
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

// #define DEBUG_PRINT 1
#define DEBUG_PRINT 0

using namespace llvm;

namespace llvm {
    void initializeRefNormalizePassPass(PassRegistry &Registry);
    void initializeRefPrunePassPass(PassRegistry &Registry);
}

bool IsIncRef(CallInst *call_inst) {
    Value *callee = call_inst->getCalledOperand();
    return callee->getName() == "NRT_incref";
}

bool IsDecRef(CallInst *call_inst) {
    Value *callee = call_inst->getCalledOperand();
    return callee->getName() == "NRT_decref";
}


CallInst* GetRefOpCall(Instruction *ii) {
    if (ii->getOpcode() == Instruction::Call) {
        CallInst *call_inst = dyn_cast<CallInst>(ii);
        if ( IsIncRef(call_inst) || IsDecRef(call_inst) ) {
            return call_inst;
        }
    }
    return NULL;
}

/**
 * Move decref after increfs
 */
struct RefNormalizePass : public FunctionPass {
    static char ID;
    RefNormalizePass() : FunctionPass(ID) {
        initializeRefNormalizePassPass(*PassRegistry::getPassRegistry());
    }

    bool runOnFunction(Function &F) override {
        bool mutated = false;
        for (BasicBlock &bb : F) {
            // Find last incref
            bool has_incref = false;
            for (Instruction &ii : bb) {
                CallInst *refop = GetRefOpCall(&ii);
                if ( refop != NULL && IsIncRef(refop) ) {
                    has_incref = true;
                    break;
                }
            }

            if (has_incref) {
                // Moves decrefs to the back just before the terminator.
                SmallVector<CallInst*, 10> to_be_moved;
                for (Instruction &ii : bb) {
                    CallInst *refop = GetRefOpCall(&ii);
                    if ( refop != NULL && IsDecRef(refop) ) {
                        to_be_moved.push_back(refop);
                    }
                }
                for (CallInst* decref : to_be_moved) {
                    decref->moveBefore(bb.getTerminator());
                    mutated |= true;
                }
            }
        }
        return mutated;
    }
};

struct RefPrunePass : public FunctionPass {
    static char ID;
    RefPrunePass() : FunctionPass(ID) {
        initializeRefPrunePassPass(*PassRegistry::getPassRegistry());
    }

    bool runOnFunction(Function &F) override {
        // errs() << "F.getName() " << F.getName() << '\n';
        // if (F.getName().startswith("_ZN7cpython5")){
        //     return false;
        // }

        auto &domtree = getAnalysis<DominatorTreeWrapperPass>().getDomTree();
        auto &postdomtree = getAnalysis<PostDominatorTreeWrapperPass>().getPostDomTree();

        // domtree.viewGraph();   // view domtree
        // postdomtree.viewGraph();

        bool mutated = false;

        // -------------------------------------------------------------------
        // Pass 1. Per BasicBlock pruning.
        // Assumes all increfs are before all decrefs.
        // Cleans up all refcount operations on NULL pointers.
        // Cleans up all incref/decref pairs.
        for (BasicBlock &bb : F) {
            SmallVector<CallInst*, 10> incref_list, decref_list, null_list;
            for (Instruction &ii : bb) {
                CallInst* ci;
                if ( (ci = GetRefOpCall(&ii)) ) {
                    if (!isNonNullFirstArg(ci)) {
                        // Drop refops on NULL pointers
                        null_list.push_back(ci);
                    } else if ( IsIncRef(ci) ) {
                        incref_list.push_back(ci);
                    }
                    else if ( IsDecRef(ci) ) {
                        decref_list.push_back(ci);
                    }
                }
            }
            // Remove refops on NULL
            for (CallInst* ci: null_list) {
                ci->eraseFromParent();
                mutated |= true;
            }
            // Find matching pairs of incref decref
            while (incref_list.size() > 0) {
                CallInst* incref = incref_list.pop_back_val();
                for (size_t i=0; i < decref_list.size(); ++i){
                    CallInst* decref = decref_list[i];
                    if (decref && isRelatedDecref(incref, decref)) {
                        if (DEBUG_PRINT) {
                            errs() << "Prune these due to DOM + PDOM:\n";
                            incref->dump();
                            decref->dump();
                            incref->getParent()->dump();
                        }
                        incref->eraseFromParent();
                        decref->eraseFromParent();

                        decref_list[i] = NULL;
                        mutated |= true;
                        break;
                    }
                }
            }

        }


        return mutated;
        // Find all incref & decref
        std::vector<CallInst*> incref_list, decref_list, null_list;
        for (BasicBlock &bb : F) {
            for (Instruction &ii : bb) {
                CallInst* ci;
                if ( (ci = GetRefOpCall(&ii)) ) {
                    if (!isNonNullFirstArg(ci)) {
                        // Drop refops on NULL pointers
                        null_list.push_back(ci);
                    } else if ( IsIncRef(ci) ) {
                        incref_list.push_back(ci);
                    }
                    else if ( IsDecRef(ci) ) {
                        decref_list.push_back(ci);
                    }
                }
            }
        }


        // Remove refops on NULL
        for (CallInst* ci: null_list) {
            ci->eraseFromParent();
            mutated |= true;
        }
        null_list.clear();

        // Check pairs that are dominating and postdominating each other
        bool diamond = false;
        for (CallInst*& incref: incref_list) {
            if (incref == NULL) continue;

            for (CallInst*& decref: decref_list) {
                if (decref == NULL) continue;

                if (incref->getArgOperand(0) != decref->getArgOperand(0) )
                    continue;

                if ( domtree.dominates(incref, decref)
                        && postdomtree.dominates(decref, incref) ){
                    // if (DEBUG_PRINT) {
                    //     errs() << "Prune these due to DOM + PDOM\n";
                    //     incref->dump();
                    //     decref->dump();

                    //     incref->dump();
                    //     errs() << "\n";
                    // }
                    if (0 && incref->getParent() != decref->getParent() ) {
                        SmallVector<BasicBlock*, 20> stack;
                        if (hasDecrefBetweenGraph(incref->getParent(), decref->getParent(), stack)) {
                            continue;
                        } else {

                            if (DEBUG_PRINT) {
                                errs() << F.getName() << "-------------\n";
                                errs() << incref->getParent()->getName() << "\n";
                                incref->dump();
                                errs() << decref->getParent()->getName() << "\n";
                                decref->dump();
                            // diamond = true;
                            }

                            // incref->eraseFromParent();
                            // decref->eraseFromParent();
                            // incref = NULL;
                            // decref = NULL;
                        }
                    }
                    else {
                        errs() << "Prune these due to DOM + PDOM: " << incref << " " << decref << "\n";
                        incref->dump();
                        decref->dump();

                        incref->getParent()->dump();
                        incref->eraseFromParent();
                        decref->eraseFromParent();

                        incref = NULL;
                        decref = NULL;
                    }
                    mutated |= true;
                    break;
                }
            }
        }
        // if (diamond) F.viewCFG();
        return mutated;

        // Deal with fanout
        // a single incref with multiple decrefs in outgoing edges
        for (CallInst*& incref : incref_list) {
            if (incref == NULL) continue;

            BasicBlock *bb = incref->getParent();
            std::vector<BasicBlock*> stack;
            std::set<BasicBlock*> decref_blocks = graphWalkhandleFanout(incref, bb, stack);
            if (decref_blocks.size()) {
                if (DEBUG_PRINT) {
                    errs() << "FANOUT prune " << decref_blocks.size() << '\n';
                    incref->dump();
                }
                for (BasicBlock* each : decref_blocks) {
                    // Remove first related decref
                    for (Instruction &ii : *each) {
                        CallInst *decref;
                        if ( (decref = isRelatedDecref(incref, &ii)) ) {
                            if (DEBUG_PRINT) {
                                decref->dump();
                            }
                            decref->eraseFromParent();
                            break;
                        }
                    }
                }
                incref->eraseFromParent();
                incref = NULL;
                mutated |= true;
            }
        }
        return mutated;
    }

    std::set<BasicBlock*> graphWalkhandleFanout(
            CallInst* incref,
            BasicBlock *cur_node,
            std::vector<BasicBlock*> stack,
            int depth=10) {
    std::set<BasicBlock*> decref_blocks;
    depth -= 1;
    if( depth <= 0 ) return decref_blocks;

    bool missing = false;
    stack.push_back(cur_node);

    // for each edge
    Instruction* term = cur_node->getTerminator();
    for (unsigned int i = 0; i < term->getNumSuccessors(); ++i) {
        BasicBlock * child = term->getSuccessor(i);
        if (basicBlockInList(child, stack)) {
            // already visited
            continue;
        } else if (hasDecrefInNode(incref, child)) {
            decref_blocks.insert(child);
        } else {
            std::set<BasicBlock*> inner = graphWalkhandleFanout(incref, child, stack, depth);
            if (inner.size() > 0) {
                // decref_blocks |= inner
                for (BasicBlock* each : inner) {
                    decref_blocks.insert(each);
                }
            } else {
                missing |= true;
            }
        }
    }
    stack.pop_back();
    if (missing) {
        decref_blocks.clear();
        return decref_blocks;
    }
    return decref_blocks;
    }

    template<class T>
    bool basicBlockInList(const BasicBlock* bb, const T &list){
        for (BasicBlock *each : list) {
            if (bb == each) return true;
        }
        return false;
    }

    bool hasDecrefInNode(CallInst* incref, BasicBlock* bb){
        for (Instruction &ii : *bb) {
            if (isRelatedDecref(incref, &ii) != NULL) {
                return true;
            }
        }
        return false;
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

    /**
     * Find related decrefs to incref inside a basicblock in order
     */
    std::vector<CallInst*> findRelatedDecrefs(BasicBlock* bb, CallInst* incref) {
        std::vector<CallInst*> res;
        for (Instruction &ii : *bb) {
        CallInst *call_inst;
        if ((call_inst = isRelatedDecref(incref, &ii))){
            res.push_back(call_inst);
        } else {
            continue;
        }
        }
        return res;
    }

    CallInst* isRelatedDecref(CallInst *incref, Instruction *ii) {
        // TODO: DRY
        if (ii->getOpcode() == Instruction::Call) {
            CallInst *call_inst = dyn_cast<CallInst>(ii);
            Value *callee = call_inst->getCalledOperand();
            if ( callee->getName() != "NRT_decref" ) {
                return NULL;
            }
            if (incref->getArgOperand(0) != call_inst->getArgOperand(0)) {
                return NULL;
            }
            return call_inst;
        }
        return NULL;
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

    /**
     * Pre-condition: head_node dominates tail_node
     */
    bool hasDecrefBetweenGraph(BasicBlock *head_node, BasicBlock *tail_node,
                               SmallVector<BasicBlock*, 20> &stack) {
        if (basicBlockInList(head_node, stack)) {
            return false;
        }
        if (DEBUG_PRINT) {
            errs() << "Check..." << head_node->getName() << "\n";
        }
        stack.push_back(head_node);
        Instruction *term = head_node->getTerminator();
        for (unsigned i=0; i < term->getNumSuccessors(); ++i) {
            BasicBlock *child = term->getSuccessor(i);
            if (child == tail_node)
                return false;
            for (Instruction &ii: *child) {
                CallInst* refop = GetRefOpCall(&ii);
                if (refop != NULL && IsDecRef(refop)) {
                    if (DEBUG_PRINT) {
                        errs() << "  No\n";
                        refop->dump();
                    }
                    return true;
                }
            }
            // XXX: Recurse
            if(hasDecrefBetweenGraph(child, tail_node, stack)){
                return true;
            }
        }
        return false;
    }
}; // end of struct RefPrunePass


char RefNormalizePass::ID = 0;
char RefPrunePass::ID = 0;

INITIALIZE_PASS_BEGIN(RefNormalizePass, "nrtrefnormalizepass",
                      "Normalize NRT refops", false, false)
INITIALIZE_PASS_END(RefNormalizePass, "nrtrefnormalizepass",
                    "Normalize NRT refops", false, false)

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
    unwrap(PM)->add(new RefNormalizePass());
    unwrap(PM)->add(new RefPrunePass());
}


} // extern "C"