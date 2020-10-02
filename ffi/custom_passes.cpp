
#include "core.h"


#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Instructions.h"

#include "llvm/ADT/SmallString.h"
#include "llvm/ADT/SmallSet.h"

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

#include <iostream>
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
    static size_t stats_per_bb;
    static size_t stats_diamond;
    static size_t stats_fanout;
    static size_t stats_fanout_raise;

    static const size_t FANOUT_RECURSE_DEPTH= 15;
    typedef SmallSet<BasicBlock*, FANOUT_RECURSE_DEPTH> SmallBBSet;

    RefPrunePass() : FunctionPass(ID) {
        initializeRefPrunePassPass(*PassRegistry::getPassRegistry());
    }

    bool runOnFunction(Function &F) override {
        // errs() << "F.getName() " << F.getName() << '\n';
        // if (F.getName().startswith("_ZN7cpython5")){
        //     return false;
        // }
        // domtree.viewGraph();   // view domtree
        // postdomtree.viewGraph();

        bool mutated = false;

        bool local_mutated;
        do {
            local_mutated = false;
            local_mutated |= runPerBasicBlockPrune(F);
            local_mutated |= runDiamondPrune(F);
            local_mutated |= runFanoutPrune(F, /*prune_raise*/false);
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
                mutated = true;
                stats_per_bb += 1;
            }
            // Find matching pairs of incref decref
            while (incref_list.size() > 0) {
                CallInst* incref = incref_list.pop_back_val();
                for (size_t i=0; i < decref_list.size(); ++i){
                    CallInst* decref = decref_list[i];
                    if (decref && isRelatedDecref(incref, decref)) {
                        if (DEBUG_PRINT) {
                            errs() << "Prune: matching pair in BB:\n";
                            incref->dump();
                            decref->dump();
                            incref->getParent()->dump();
                        }
                        incref->eraseFromParent();
                        decref->eraseFromParent();

                        decref_list[i] = NULL;
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
        auto &domtree = getAnalysis<DominatorTreeWrapperPass>().getDomTree();
        auto &postdomtree = getAnalysis<PostDominatorTreeWrapperPass>().getPostDomTree();

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

        for (CallInst*& incref: incref_list) {
            if (incref == NULL) continue;

            for (CallInst*& decref: decref_list) {
                if (decref == NULL) continue;

                // Not the same BB
                if (incref->getParent() == decref->getParent() ) continue;

                // Is related refop pair
                if (!isRelatedDecref(incref, decref)) continue;

                // incref DOM decref && decref POSTDOM incref
                if ( domtree.dominates(incref, decref)
                        && postdomtree.dominates(decref, incref) ){

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
                        }

                        incref->eraseFromParent();
                        decref->eraseFromParent();
                        incref = NULL;
                        decref = NULL;

                        stats_diamond += 2;
                    }
                    mutated |= true;
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
                // be v with potential alias
                continue;  // skip
            }

            SmallBBSet decref_blocks;
            if ( findFanout(incref, &decref_blocks, prune_raise_exit) ) {
                // Remove first related decref in each block
                if (0||DEBUG_PRINT) {
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
                            if (0||DEBUG_PRINT) {
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

                // int wait;
                // std::cin >> wait;
            }
        }
        return mutated;
    }

    bool findFanout(CallInst *incref, SmallBBSet *decref_blocks, bool prune_raise_exit) {
        BasicBlock *head_node = incref->getParent();
        SmallBBSet raising_blocks, *p_raising_blocks = NULL;
        if( prune_raise_exit ) p_raising_blocks = &raising_blocks;

        if ( findFanoutDecrefCandidates(incref, head_node, decref_blocks, p_raising_blocks) ) {
            if (0||DEBUG_PRINT) {
                errs() << "forward pass candids.size() = " << decref_blocks->size() << "\n";
                errs() << "    " << head_node->getName() << "\n";
                incref->dump();
            }
            if (decref_blocks->size() == 0) {
                // no decref blocks
                if (0||DEBUG_PRINT) {
                    errs() << "missing decref blocks = " << raising_blocks.size() << "\n";
                }
                return false;
            }
            if ( prune_raise_exit ) {
                if ( raising_blocks.size() == 0) {
                    // no raising blocks
                    if (0||DEBUG_PRINT) {
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

    bool runFanoutPruneOld(Function &F, bool prune_raise_exit) {
        bool mutated = false;
        auto &domtree = getAnalysis<DominatorTreeWrapperPass>().getDomTree();
        auto &postdomtree = getAnalysis<PostDominatorTreeWrapperPass>().getPostDomTree();

        // Deal with fanout
        // a single incref with multiple decrefs in outgoing edges

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

        // bool view_cfg = false;
        int mask = 0;
        mask |= 1;
        if (prune_raise_exit) {
            mask |= 2;
        }

        for (CallInst* incref : incref_list) {
            BasicBlock *bb = incref->getParent();
            std::set<BasicBlock*> decref_blocks, ban_list;
            // if (hasAnyDecrefInNode(bb)) continue;
            int status = graphWalkHandleFanout(incref, bb, domtree, prune_raise_exit, decref_blocks, ban_list);

            for (BasicBlock* banned : ban_list) {
                if ( decref_blocks.find(banned) != decref_blocks.end() ){
                    status = 0;
                    break;
                }
            }
            if ( status == mask && status > 0) {
                if (DEBUG_PRINT) {
                    errs() << "FANOUT prune " << decref_blocks.size() << '\n';
                    errs() << incref->getParent()->getName() << "\n";
                    incref->dump();
                }
                // Check if any block dominates other blocks
                if (checkCrossDominate(decref_blocks, postdomtree)) {
                    if (DEBUG_PRINT) {
                        errs() << "FANOUT prune cancelled due to cross dominating\n";
                    }
                    continue;
                }

                // if (prune_raise_exit) {
                //     errs() << "FANOUT prune " << decref_blocks.size() << '\n';
                //     errs() << incref->getParent()->getName() << "\n";
                //     incref->dump();
                //     for (BasicBlock* each : decref_blocks) {
                //         errs() << "    " << each->getName() << "\n";
                //     }


                //     std::cout<< "wait ";
                //     int do_print;
                //     std::cin >> do_print;
                //     if (do_print){
                //         F.viewCFG();
                //         domtree.viewGraph();
                //         }
                // }

                // Remove first related decref in each block
                for (BasicBlock* each : decref_blocks) {
                    for (Instruction &ii : *each) {
                        CallInst *decref;
                        if ( (decref = isRelatedDecref(incref, &ii)) ) {
                            if (DEBUG_PRINT) {
                                errs() << decref->getParent()->getName() << "\n";
                                decref->dump();
                            }
                            decref->eraseFromParent();
                            // view_cfg = true;
                            break;
                        }
                    }
                }
                incref->eraseFromParent();
                mutated |= true;

                if ((status & 2) == 2) stats_fanout_raise += 1;
                else                   stats_fanout += 1;


            }
        }

        // if (!mutated) {
        //     if (F.getName() == "_ZN8__main__7foo$241E5ArrayIxLi2E1C7mutable7alignedE")
        //         domtree.viewGraph();
        // }
        // if (view_cfg) {
        //     F.viewCFG();
        // }
        return mutated;
    }

    bool checkCrossDominate(const std::set<BasicBlock*> blocks, PostDominatorTree& pdomtree){
        for (BasicBlock* M : blocks) {
            for (BasicBlock* N : blocks) {
                if (M != N) {
                    if (pdomtree.dominates(M, N)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    int graphWalkHandleFanout(CallInst* incref,
                               BasicBlock *cur_node,
                               DominatorTree &domtree,
                               bool prune_raise_exit,
                               std::set<BasicBlock*> &decref_blocks,
                               std::set<BasicBlock*> &ban_list,
                               int depth=10)
    {
        depth -= 1;
        if( depth <= 0 ) return 0;

        // for each domtree children
        auto domnode = domtree.getNode(cur_node);

        int status = 0, inner_status;

        for (auto domchild : domnode->getChildren()){
            BasicBlock *child = domchild->getBlock();
            if (hasDecrefInNode(incref, child) && notInLoop(child, domtree)) {
                decref_blocks.insert(child);

                SmallVector<BasicBlock*, 5> descs;
                domtree.getDescendants(child, descs);
                for (auto desc : descs) {
                    if (desc != child)
                        ban_list.insert(desc);
                }

                status |= 1;
            } else if (prune_raise_exit && isRaising(child)) {
                decref_blocks.insert(child);
                status |= 2;
            } else if ( (inner_status=graphWalkHandleFanout(incref, child, domtree, prune_raise_exit, decref_blocks, ban_list, depth)) ) {
                // if (hasAnyDecrefInNode(child)) return 0;
                status |= inner_status;
            } else {
                return 0;
            }
        }

        return status;
    }

    bool notInLoop(const BasicBlock* bb, DominatorTree& domtree) {
        auto term = bb->getTerminator();
        for (unsigned i=0; i<term->getNumSuccessors(); ++i){
            auto succ = term->getSuccessor(i);
            if (domtree.dominates(succ, bb)) {
                return false;  // is backedge
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
    bool hasDecrefBetweenGraph(BasicBlock *head_node, BasicBlock *tail_node,
                               SmallVector<BasicBlock*, 20> &stack) {
        if (basicBlockInList(head_node, stack)) {
            return false;
        }
        if (DEBUG_PRINT) {
            errs() << "Check..." << head_node->getName() << "\n";
        }

        if (hasAnyDecrefInNode(head_node)) return true;

        stack.push_back(head_node);
        Instruction *term = head_node->getTerminator();
        for (unsigned i=0; i < term->getNumSuccessors(); ++i) {
            BasicBlock *child = term->getSuccessor(i);
            if (child == tail_node)
                continue;
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

size_t RefPrunePass::stats_per_bb = 0;
size_t RefPrunePass::stats_diamond = 0;
size_t RefPrunePass::stats_fanout = 0;
size_t RefPrunePass::stats_fanout_raise = 0;

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
