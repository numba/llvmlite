
#include "core.h"


#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"

#include "llvm/ADT/SmallSet.h"

#include "llvm/Support/raw_ostream.h"
#include "llvm/Analysis/Passes.h"
#include "llvm/Analysis/PostDominators.h"

#include "llvm/IR/LegacyPassManager.h"

#include "llvm/InitializePasses.h"
#include "llvm/LinkAllPasses.h"

#include <iostream>
#include <vector>

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
 * RAII push-pop of element into stack.
 */
template <class Tstack>
struct raiiStack {
    Tstack &stack;

    typedef typename Tstack::value_type value_type;

    raiiStack(Tstack &stack, value_type& elem) :stack(stack) {
        stack.push_back(elem);
    }
    ~raiiStack() {
        stack.pop_back();
    }
};

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
            // Find a incref in the basicblock
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
                // walk the instructions in the block
                for (Instruction &ii : bb) {
                    // query the instruction, if its a refop store to refop
                    // if not store NULL to refop
                    CallInst *refop = GetRefOpCall(&ii);
                    // if the refop is not NULL and it is also a decref then
                    // shove it into the to_be_moved vector
                    if ( refop != NULL && IsDecRef(refop) ) {
                        to_be_moved.push_back(refop);
                    }
                }
                // Walk the to_be_moved vector of instructions, these are all
                // decrefs by construction.
                for (CallInst* decref : to_be_moved) {
                    // move the decref to a location prior to the block
                    // terminator and set mutated.
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
    static size_t stats_per_bb;
    static size_t stats_diamond;
    static size_t stats_fanout;
    static size_t stats_fanout_raise;

    static const size_t FANOUT_RECURSE_DEPTH= 15;
    typedef SmallSet<BasicBlock*, FANOUT_RECURSE_DEPTH> SmallBBSet;

    enum Subpasses {
        None            = 0,
        PerBasicBlock   = 1,
        Diamond         = 1 << 1,
        Fanout          = 1 << 2,
        FanoutRaise     = 1 << 3,
        All             = PerBasicBlock | Diamond | Fanout | FanoutRaise
    } flags;

    RefPrunePass(Subpasses flags=Subpasses::All) : FunctionPass(ID), flags(flags) {
        initializeRefPrunePassPass(*PassRegistry::getPassRegistry());
    }

    bool isSubpassEnabledFor(Subpasses expected) {
        return (flags & expected) == expected;
    }

    bool runOnFunction(Function &F) override {
        bool mutated = false;

        bool local_mutated;
        do {
            local_mutated = false;
            if (isSubpassEnabledFor(Subpasses::PerBasicBlock))
                local_mutated |= runPerBasicBlockPrune(F);
            if (isSubpassEnabledFor(Subpasses::Diamond))
                local_mutated |= runDiamondPrune(F);
            if (isSubpassEnabledFor(Subpasses::Fanout))
                local_mutated |= runFanoutPrune(F, /*prune_raise*/false);
            if (isSubpassEnabledFor(Subpasses::FanoutRaise))
                local_mutated |= runFanoutPrune(F, /*prune_raise*/true);
            mutated |= local_mutated;
        } while(local_mutated);

        return mutated;
    }

    bool runPerBasicBlockPrune(Function &F) {
        // -------------------------------------------------------------------
        // Pass 1. Per BasicBlock pruning.
        // Assumes all increfs are before all decrefs.
        // Cleans up all refcount operations on NULL pointers.
        // Cleans up all incref/decref pairs.
        bool mutated = false;

        // walk the basic blocks in Function F.
        for (BasicBlock &bb : F) {
            // allocate some buffers
            SmallVector<CallInst*, 10> incref_list, decref_list, null_list;

            // This is a scanning phase looking to classify instructions into
            // inrefs, decrefs and operations on already NULL pointers.
            // walk the instructions in the current basic block
            for (Instruction &ii : bb) {
                // If the instruction is a refop
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

            // First: Remove refops on NULL
            for (CallInst* ci: null_list) {
                ci->eraseFromParent();
                mutated = true;

                // Do we care about differentiating between prunes of NULL
                // and prunes of pairs?
                stats_per_bb += 1;
            }

            // Second: Find matching pairs of incref decref
            while (incref_list.size() > 0) {
                // get an incref
                CallInst* incref = incref_list.pop_back_val();
                // walk decrefs
                for (size_t i=0; i < decref_list.size(); ++i){
                    CallInst* decref = decref_list[i];
                    // is this instruction a decref thats non-NULL and
                    // the decref related to the incref?
                    if (decref && isRelatedDecref(incref, decref)) {
                        if (DEBUG_PRINT) {
                            errs() << "Prune: matching pair in BB:\n";
                            incref->dump();
                            decref->dump();
                            incref->getParent()->dump();
                        }
                        // strip incref and decref from blck
                        incref->eraseFromParent();
                        decref->eraseFromParent();

                        // set stripped decref to null
                        decref_list[i] = NULL;
                        // set mutated bit and update prune stats
                        mutated = true;
                        stats_per_bb += 2;
                        break;
                    }
                }
            }
        }
        return mutated;
    }

    bool runDiamondPrune(Function &F) {
        // Check pairs that are dominating and postdominating each other
        bool mutated = false;
        // gets the dominator tree
        auto &domtree = getAnalysis<DominatorTreeWrapperPass>().getDomTree();
        // gets the post-dominator tree
        auto &postdomtree = getAnalysis<PostDominatorTreeWrapperPass>().getPostDomTree();

        // Scan for inrefs and decrefs within the function blocks
        // TODO: DRY? seems to be a common thing.
        std::vector<CallInst*> incref_list, decref_list;
        for (BasicBlock &bb : F) {
            for (Instruction &ii : bb) {
                CallInst* ci;
                if ( (ci = GetRefOpCall(&ii)) ) {
                    if ( IsIncRef(ci) ) {
                        incref_list.push_back(ci);
                    }
                    else if ( IsDecRef(ci) ) {
                        decref_list.push_back(ci);
                    }
                }
            }
        }

        // Walk the incref list
        for (CallInst*& incref: incref_list) {
            // NULL is the token for already erased, skip on it
            if (incref == NULL) continue;

            // Walk the decref_list
            for (CallInst*& decref: decref_list) {
                // NULL is the token for already erased, skip on it
                if (decref == NULL) continue;

                // Diamond prune is for refops not in the same BB
                if (incref->getParent() == decref->getParent() ) continue;

                // If the refops are unrelated, skip
                if (!isRelatedDecref(incref, decref)) continue;

                // incref DOM decref && decref POSTDOM incref
                if ( domtree.dominates(incref, decref)
                        && postdomtree.dominates(decref, incref) ){

                    // scan the CFG between the incref and decref BBs, if there's a decref
                    // present then skip, this is conservative.
                    if (hasDecrefBetweenGraph(incref->getParent(), decref->getParent())) {
                        continue;
                    } else {

                        if (DEBUG_PRINT) {
                            errs() << F.getName() << "-------------\n";
                            errs() << incref->getParent()->getName() << "\n";
                            incref->dump();
                            errs() << decref->getParent()->getName() << "\n";
                            decref->dump();
                        }

                        // erase instruction from block and set NULL marker for
                        // bookkeeping purposes
                        incref->eraseFromParent();
                        decref->eraseFromParent();
                        incref = NULL;
                        decref = NULL;

                        stats_diamond += 2;
                    }
                    // mark mutated
                    mutated = true;
                    break;
                }
            }
        }
        return mutated;
    }

    bool runFanoutPrune(Function &F, bool prune_raise_exit) {
        bool mutated = false;

        // Find Incref
        std::vector<CallInst*> incref_list;
        for (BasicBlock &bb : F) {
            for (Instruction &ii : bb) {
                CallInst* ci;
                if ( (ci = GetRefOpCall(&ii)) ) {
                    if ( IsIncRef(ci) ) {
                        incref_list.push_back(ci);
                    }
                }
            }
        }

        for (CallInst* incref : incref_list) {
            if (hasAnyDecrefInNode(incref->getParent())){
                // becarefull of potential alias
                continue;  // skip
            }

            SmallBBSet decref_blocks;
            if ( findFanout(incref, &decref_blocks, prune_raise_exit) ) {
                // Remove first related decref in each block
                if (DEBUG_PRINT) {
                    F.viewCFG();
                    errs() << "------------\n";
                    errs() << "incref " << incref->getParent()->getName() << "\n" ;
                    errs() << "  decref_blocks.size()" << decref_blocks.size() << "\n" ;
                    incref->dump();

                }
                for (BasicBlock* each : decref_blocks) {
                    for (Instruction &ii : *each) {
                        CallInst *decref;
                        if ( (decref = isRelatedDecref(incref, &ii)) ) {
                            if (DEBUG_PRINT) {
                                errs() << decref->getParent()->getName() << "\n";
                                decref->dump();
                            }
                            decref->eraseFromParent();

                            if (prune_raise_exit)   stats_fanout_raise += 1;
                            else                    stats_fanout += 1;
                            break;
                        }
                    }
                }
                incref->eraseFromParent();

                if (prune_raise_exit)   stats_fanout_raise += 1;
                else                    stats_fanout += 1;
                mutated = true;
            }
        }
        return mutated;
    }

    bool findFanout(CallInst *incref, SmallBBSet *decref_blocks, bool prune_raise_exit) {
        BasicBlock *head_node = incref->getParent();
        SmallBBSet raising_blocks, *p_raising_blocks = NULL;
        if( prune_raise_exit ) p_raising_blocks = &raising_blocks;

        if ( findFanoutDecrefCandidates(incref, head_node, decref_blocks, p_raising_blocks) ) {
            if (DEBUG_PRINT) {
                errs() << "forward pass candids.size() = " << decref_blocks->size() << "\n";
                errs() << "    " << head_node->getName() << "\n";
                incref->dump();
            }
            if (decref_blocks->size() == 0) {
                // no decref blocks
                if (DEBUG_PRINT) {
                    errs() << "missing decref blocks = " << raising_blocks.size() << "\n";
                }
                return false;
            }
            if ( prune_raise_exit ) {
                if ( raising_blocks.size() == 0) {
                    // no raising blocks
                    if (DEBUG_PRINT) {
                        errs() << "missing raising blocks = " << raising_blocks.size() << "\n";
                        for (auto bb : *decref_blocks){
                            errs() << "   " << bb->getName() << "\n";
                        }
                    }
                    return false;
                }

                // combine decref_blocks into raising blocks for checking the exit node condition
                for ( BasicBlock* bb : *decref_blocks ) {
                    raising_blocks.insert(bb);
                }
                if ( verifyFanoutBackward(incref, head_node, p_raising_blocks) )
                    return true;

            } else if ( verifyFanoutBackward(incref, head_node, decref_blocks) ) {
                return true;
            }
        }
        return false;
    }

    /**
     * Forward pass.
     *
     * Walk the successors of the incref node recursively until a decref
     * or an exit node is found.
     * If an exit node is found and raising_blocks is non-NULL,
     * check if it is raising and store the raising block into raising_blocks.
     *
     * Return condition:
     *   depends on raising_blocks:
     *      == NULL -> return true iff all paths have led to a decref.
     *      != NULL -> return true iff all paths have led to
     *                 a decref or a raising exit.
     */
    bool findFanoutDecrefCandidates(CallInst *incref,
                                    BasicBlock *cur_node,
                                    SmallBBSet *decref_blocks,
                                    SmallBBSet *raising_blocks) {
        SmallVector<BasicBlock*, FANOUT_RECURSE_DEPTH> path_stack;
        bool found = false;
        auto term = cur_node->getTerminator();

        raiiStack<SmallVectorImpl<BasicBlock*>> raii_path_stack(path_stack, cur_node);

        for ( unsigned i=0; i<term->getNumSuccessors(); ++i) {
            BasicBlock *child = term->getSuccessor(i);
            found = walkChildForDecref(
                incref, child, path_stack, decref_blocks, raising_blocks
            );
            if (!found) return false;
        }
        return found;
    }

    bool walkChildForDecref(
        CallInst *incref,
        BasicBlock *cur_node,
        SmallVectorImpl<BasicBlock*> &path_stack,
        SmallBBSet *decref_blocks,
        SmallBBSet *raising_blocks
    ) {
        if ( path_stack.size() >= FANOUT_RECURSE_DEPTH ) return false;

        // check for backedge
        if ( basicBlockInList(cur_node, path_stack) ) {
            if ( cur_node == path_stack[0] ) {
                // Reject interior node backedge to start of subgraph.
                // This means that the incref can be executed multiple times
                // before reaching the decref.
                return false;
            }
            // is a legal backedge; skip
            return true;
        }

        // Does this block has a related decref?
        if ( hasDecrefInNode(incref, cur_node) ) {
            decref_blocks->insert(cur_node);
            return true;  // done for this path
        }

        if ( hasAnyDecrefInNode(cur_node) ) {
            // Because we don't know about aliasing
            return false;
        }

        // checking for raise blocks
        if (raising_blocks && isRaising(cur_node)) {
            raising_blocks->insert(cur_node);
            return true;  // done for this path
        }

        // recurse into predecessors of the current block.
        raiiStack<SmallVectorImpl<BasicBlock*> > raii_push_pop(path_stack, cur_node);
        bool found = false;
        auto term = cur_node->getTerminator();
        for ( unsigned i=0; i<term->getNumSuccessors(); ++i) {
            BasicBlock *child = term->getSuccessor(i);
            found = walkChildForDecref(
                incref, child, path_stack, decref_blocks, raising_blocks
            );
            if (!found) return false;
        }
        // If this is a leaf node, returns false.
        return found;
    }

    /**
     * Backward pass.
     * Check the tail-node condition for the fanout subgraph.
     * The reverse walks from all exit-nodes must end with the head-node.
     */
    bool verifyFanoutBackward(
        CallInst *incref,
        BasicBlock *head_node,
        const SmallBBSet *tail_nodes
    ) {
        SmallVector<BasicBlock*, 10> todo;
        for (BasicBlock *bb: *tail_nodes) {
            todo.push_back(bb);
        }

        SmallBBSet visited;
        while (todo.size() > 0) {
            SmallVector<BasicBlock*, FANOUT_RECURSE_DEPTH> workstack;
            workstack.push_back(todo.pop_back_val());

            while (workstack.size() > 0) {
                BasicBlock *cur_node = workstack.pop_back_val();
                if ( visited.count(cur_node) ) {
                    // Already visited
                    continue;  // skip
                }

                if ( cur_node == &head_node->getParent()->getEntryBlock() ) {
                    // Arrived at the entry node of the function.
                    // This means the reverse walk from a tail-node can
                    // bypass the head-node (incref node) of this fanout
                    // subgraph.
                    return false;
                }

                // remember that we have visited this node already
                visited.insert(cur_node);

                // Walk into all predecessors
                auto it = pred_begin(cur_node), end = pred_end(cur_node);
                for (; it != end; ++it ) {
                    auto pred = *it;
                    if ( tail_nodes->count(pred) ) {
                        // reject because a predecessor is a decref_block
                        return false;
                    }
                    if ( pred != head_node ) {
                        // If the predecessor is the head-node,
                        // this path is ok; otherwise, continue to walk up.
                        workstack.push_back(pred);
                    }
                }
            }
        }
        return true;
    }

    bool isRaising(const BasicBlock* bb) {
        auto term = bb->getTerminator();
        if (term->getOpcode() != Instruction::Ret)
            return false;
        auto md = term->getMetadata("ret_is_raise");
        if (!md)
            return false;
        if (md->getNumOperands() != 1)
            return false;
        auto &operand = md->getOperand(0);
        auto data = dyn_cast<ConstantAsMetadata>(operand.get());
        if (!data)
            return false;
        return data->getValue()->isOneValue();
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

    bool hasAnyDecrefInNode(BasicBlock *bb) {

        for (Instruction &ii: *bb) {
            CallInst* refop = GetRefOpCall(&ii);
            if (refop != NULL && IsDecRef(refop)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Pre-condition: head_node dominates tail_node
     */
    bool hasDecrefBetweenGraph(BasicBlock *head_node, BasicBlock *tail_node) {
        // This function implements a depth-first search.

        // visited keeps track of the visited blocks
        SmallBBSet visited;
        // stack keeps track of blocks to be checked.
        SmallVector<BasicBlock*, 20> stack;
        // start with the head_node;
        stack.push_back(head_node);
        do {
            BasicBlock *cur_node = stack.pop_back_val();
            // First, Is the current BB already visited, if so return false,
            // its already been checked.
            if (visited.count(cur_node)) {
                continue; // skip
            }
            // remember that it is visited
            visited.insert(cur_node);
            if (DEBUG_PRINT) {
                errs() << "Check..." << cur_node->getName() << "\n";
            }

            // scan the current BB for decrefs, if any are present return true
            if (hasAnyDecrefInNode(cur_node)) return true;

            // get the terminator of the cur node
            Instruction *term = cur_node->getTerminator();
            // walk the successor blocks
            for (unsigned i=0; i < term->getNumSuccessors(); ++i) {
                BasicBlock *child = term->getSuccessor(i);
                // if the successor is the tail node, skip
                if (child == tail_node)
                    continue;
                // else check the subgraph between the current successor and the
                // tail
                stack.push_back(child);
            }
        } while(stack.size() > 0);
        return false;
    }
}; // end of struct RefPrunePass


char RefNormalizePass::ID = 0;
char RefPrunePass::ID = 0;

size_t RefPrunePass::stats_per_bb = 0;
size_t RefPrunePass::stats_diamond = 0;
size_t RefPrunePass::stats_fanout = 0;
size_t RefPrunePass::stats_fanout_raise = 0;

INITIALIZE_PASS(RefNormalizePass, "nrtrefnormalizepass",
                "Normalize NRT refops", false, false)

INITIALIZE_PASS_BEGIN(RefPrunePass, "nrtrefprunepass",
                      "Prune NRT refops", false, false)
INITIALIZE_PASS_DEPENDENCY(DominatorTreeWrapperPass)
INITIALIZE_PASS_DEPENDENCY(PostDominatorTreeWrapperPass)

INITIALIZE_PASS_END(RefPrunePass, "refprunepass",
                    "Prune NRT refops", false, false)
extern "C" {

API_EXPORT(void)
LLVMPY_AddRefPrunePass(LLVMPassManagerRef PM, int subpasses)
{
    unwrap(PM)->add(new RefNormalizePass());
    unwrap(PM)->add(new RefPrunePass((RefPrunePass::Subpasses)subpasses));
}


typedef struct PruneStats {
    size_t basicblock;
    size_t diamond;
    size_t fanout;
    size_t fanout_raise;
} PRUNESTATS;


API_EXPORT(void)
LLVMPY_DumpRefPruneStats(PRUNESTATS *buf, bool do_print)
{
    /* PRUNESTATS is updated with the statistics about what has been pruned from
     * the RefPrunePass static state vars. This isn't threadsafe but neither is
     * the LLVM pass infrastructure so it's all done under a python thread lock.
     *
     * do_print if set will print the stats to stderr.
     */
    if (do_print) {
        errs() << "refprune stats "
            << "per-BB " << RefPrunePass::stats_per_bb << " "
            << "diamond " << RefPrunePass::stats_diamond << " "
            << "fanout " << RefPrunePass::stats_fanout << " "
            << "fanout+raise " << RefPrunePass::stats_fanout_raise << " "
            << "\n";
    };

    buf->basicblock = RefPrunePass::stats_per_bb;
    buf->diamond = RefPrunePass::stats_diamond;
    buf->fanout = RefPrunePass::stats_fanout;
    buf->fanout_raise = RefPrunePass::stats_fanout_raise;
}


} // extern "C"
