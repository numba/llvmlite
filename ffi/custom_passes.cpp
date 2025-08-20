
#include "core.h"

#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Pass.h"

#include "llvm/ADT/SmallSet.h"

#include "llvm/Analysis/Passes.h"
#include "llvm/Analysis/PostDominators.h"
#include "llvm/Support/raw_ostream.h"

#include "llvm/InitializePasses.h"
#include "llvm/LinkAllPasses.h"

#include <iostream>
#include <vector>

// #define DEBUG_PRINT 1
#define DEBUG_PRINT 0

using namespace llvm;

namespace llvm {
struct OpaqueModulePassManager;
typedef OpaqueModulePassManager *LLVMModulePassManagerRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(ModulePassManager, LLVMModulePassManagerRef)

struct OpaqueFunctionPassManager;
typedef OpaqueFunctionPassManager *LLVMFunctionPassManagerRef;
DEFINE_SIMPLE_CONVERSION_FUNCTIONS(FunctionPassManager,
                                   LLVMFunctionPassManagerRef)
} // namespace llvm

namespace {
/**
 * Checks if a call instruction is an incref
 *
 * Parameters:
 *  - call_inst, a call instruction
 *
 * Returns:
 *  - true if call_inst is an incref, false otherwise
 */
bool IsIncRef(CallInst *call_inst) {
    Value *callee = call_inst->getCalledOperand();
    return callee->getName() == "NRT_incref";
}

/**
 * Checks if a call instruction is an decref
 *
 * Parameters:
 *  - call_inst, a call instruction
 *
 * Returns:
 *  - true if call_inst is an decref, false otherwise
 */
bool IsDecRef(CallInst *call_inst) {
    Value *callee = call_inst->getCalledOperand();
    return callee->getName() == "NRT_decref";
}

/**
 * Checks if an instruction is a "refop" (either an incref or a decref).
 *
 * Parameters:
 *  - ii, the instruction to check
 *
 * Returns:
 *  - the instruction ii, if it is a "refop", NULL otherwise
 */
CallInst *GetRefOpCall(Instruction *ii) {
    if (ii->getOpcode() == Instruction::Call) {
        CallInst *call_inst = dyn_cast<CallInst>(ii);
        if (IsIncRef(call_inst) || IsDecRef(call_inst)) {
            return call_inst;
        }
    }
    return NULL;
}

/**
 * RAII push-pop of elements onto a stack.
 *
 * Template parameter <Tstack>:
 *  - the type of the stack
 */
template <class Tstack> struct raiiStack {
    Tstack &stack;

    typedef typename Tstack::value_type value_type;

    /**
     * ctor pushes `elem` onto `stack`
     */
    raiiStack(Tstack &stack, value_type &elem) : stack(stack) {
        stack.push_back(elem);
    }
    /**
     * dtor pops back of `stack`
     */
    ~raiiStack() { stack.pop_back(); }
};

/**
 * A FunctionPass to reorder incref/decref instructions such that decrefs occur
 * logically after increfs. This is a pre-requisite pass to the pruner passes.
 */
struct RefNormalize {

    bool runOnFunction(Function &F) {
        bool mutated = false;
        // For each basic block in F
        for (BasicBlock &bb : F) {
            // This find a incref in the basic block

            bool has_incref = false;
            // check the instructions in the basic block
            for (Instruction &ii : bb) {
                // see if it is a refop
                CallInst *refop = GetRefOpCall(&ii);
                // if it is a refop and it is an incref, set flag and break
                if (refop != NULL && IsIncRef(refop)) {
                    has_incref = true;
                    break;
                }
            }

            // block has an incref
            if (has_incref) {
                // This moves decrefs to the back just before the terminator.

                SmallVector<CallInst *, 10> to_be_moved;
                // walk the instructions in the block
                for (Instruction &ii : bb) {
                    // query the instruction, if its a refop store to refop
                    // if not store NULL to refop
                    CallInst *refop = GetRefOpCall(&ii);
                    // if the refop is not NULL and it is also a decref then
                    // shove it into the to_be_moved vector
                    if (refop != NULL && IsDecRef(refop)) {
                        to_be_moved.push_back(refop);
                    }
                }
                // Walk the to_be_moved vector of instructions, these are all
                // decrefs by construction.
                for (CallInst *decref : to_be_moved) {
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

typedef enum {
    None = 0b0000,
    PerBasicBlock = 0b0001,
    Diamond = 0b0010,
    Fanout = 0b0100,
    FanoutRaise = 0b1000,
    All = PerBasicBlock | Diamond | Fanout | FanoutRaise
} Subpasses;

struct RefPrune {
    static char ID;
    static size_t stats_per_bb;
    static size_t stats_diamond;
    static size_t stats_fanout;
    static size_t stats_fanout_raise;

    // Fixed size for how deep to recurse in the fanout case prior to giving up.
    static const size_t FANOUT_RECURSE_DEPTH = 15;
    typedef SmallSet<BasicBlock *, FANOUT_RECURSE_DEPTH> SmallBBSet;

    DominatorTree &DT;
    PostDominatorTree &PDT;
    /**
     * Enum for setting which subpasses to run, there is no interdependence.
     */
    Subpasses flags;

    // The maximum number of nodes that the fanout pruners will look at.
    size_t subgraph_limit;

    RefPrune(DominatorTree &DT, PostDominatorTree &PDT,
             Subpasses flags = Subpasses::All, size_t subgraph_limit = -1)
        : DT(DT), PDT(PDT), flags(flags), subgraph_limit(subgraph_limit) {}

    bool isSubpassEnabledFor(Subpasses expected) {
        return (flags & expected) == expected;
    }

    bool runOnFunction(Function &F) {
        // state for LLVM function pass mutated IR
        bool mutated = false;

        // local state for capturing mutation by any selected pass, any mutation
        // at all propagates into mutated for return.
        bool local_mutated;
        do {
            local_mutated = false;
            if (isSubpassEnabledFor(Subpasses::PerBasicBlock))
                local_mutated |= runPerBasicBlockPrune(F);
            if (isSubpassEnabledFor(Subpasses::Diamond))
                local_mutated |= runDiamondPrune(F);
            if (isSubpassEnabledFor(Subpasses::Fanout))
                local_mutated |= runFanoutPrune(F, /*prune_raise*/ false);
            if (isSubpassEnabledFor(Subpasses::FanoutRaise))
                local_mutated |= runFanoutPrune(F, /*prune_raise*/ true);
            mutated |= local_mutated;
        } while (local_mutated);

        return mutated;
    }

    /**
     * Per BasicBlock pruning pass.
     *
     * Assumes all increfs are before all decrefs.
     * Cleans up all refcount operations on NULL pointers.
     * Cleans up all redundant incref/decref pairs.
     *
     * This pass works on a block at a time and does not change the CFG.
     * Incref/Decref removal is restricted to the basic block.
     *
     * General idea is to be able to prune within a block as follows:
     *
     * ┌─────────────┐
     * │ Block entry │
     * | Instruction │
     * | Incref(A)   │ ──> No match, cannot remove.
     * | Incref(B)   │ ──┐
     * | Instruction │   │ Matching pair, can be removed.
     * | Instruction │   │
     * | Decref(B)   │ <─┘
     * | Instruction │
     * | Decref(NULL)│ ──> Decref on NULL, can be removed.
     * | Terminator  │
     * └─────────────┘
     * Parameters:
     *  - F a Function
     *
     * Returns:
     *  - true if pruning took place, false otherwise
     *
     */
    bool runPerBasicBlockPrune(Function &F) {
        bool mutated = false;

        // walk the basic blocks in Function F.
        for (BasicBlock &bb : F) {
            // allocate some buffers
            SmallVector<CallInst *, 10> incref_list, decref_list, null_list;

            // This is a scanning phase looking to classify instructions into
            // inrefs, decrefs and operations on already NULL pointers.
            // walk the instructions in the current basic block
            for (Instruction &ii : bb) {
                // If the instruction is a refop
                CallInst *ci;
                if ((ci = GetRefOpCall(&ii))) {
                    if (!isNonNullFirstArg(ci)) {
                        // Drop refops on NULL pointers
                        null_list.push_back(ci);
                    } else if (IsIncRef(ci)) {
                        incref_list.push_back(ci);
                    } else if (IsDecRef(ci)) {
                        decref_list.push_back(ci);
                    }
                }
            }

            // First: Remove refops on NULL
            for (CallInst *ci : null_list) {
                ci->eraseFromParent();
                mutated = true;

                // Do we care about differentiating between prunes of NULL
                // and prunes of pairs?
                stats_per_bb += 1;
            }

            // Second: Find matching pairs of incref decref
            while (incref_list.size() > 0) {
                // get an incref
                CallInst *incref = incref_list.pop_back_val();
                // walk decrefs
                for (size_t i = 0; i < decref_list.size(); ++i) {
                    CallInst *decref = decref_list[i];
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

    /**
     * "Diamond" pruning pass.
     *
     * Looks to prune across basic blocks in cases where incref/decref pairs
     * appear in a "diamond" shape CFG structure. For example:
     *
     *           ┌────────────┐
     *           │ incref (A) │
     *           └────────────┘
     *             /        \
     *            /          \
     *           /            \
     *          .              .
     *          .              .
     *   ┌────────────┐ ┌────────────┐
     *   │ MORE CFG   │ │ MORE CFG   │
     *   └────────────┘ └────────────┘
     *          .              .
     *          .              .
     *           \            /
     *            \          /
     *             \        /
     *              \      /
     *           ┌────────────┐
     *           │ decref (A) │
     *           └────────────┘
     *
     * Condition for prune is that, in an incref/decref pair:
     * - the incref dominates the decref.
     * - the decref postdominates the incref.
     * - in the blocks in the CFG between the basic blocks containing the
     *   incref/decref pair there's no other decref present (this is
     *   conservative and is to handle aliasing of references).
     * - that the decref is not in a cycle dominated by the incref (i.e. decref
     *   in a loop).
     *
     * Parameters:
     *  - F a Function
     *
     * Returns:
     *  - true if pruning took place, false otherwise
     *
     */
    bool runDiamondPrune(Function &F) {
        bool mutated = false;

        // Find all increfs and decrefs in the Function and store them in
        // incref_list and decref_list respectively.
        std::vector<CallInst *> incref_list, decref_list;
        listRefOps(F, IsIncRef, incref_list);
        listRefOps(F, IsDecRef, decref_list);

        // Walk the incref list
        for (CallInst *&incref : incref_list) {
            // NULL is the token for already erased, skip on it
            if (incref == NULL)
                continue;

            // Walk the decref_list
            for (CallInst *&decref : decref_list) {
                // NULL is the token for already erased, skip on it
                if (decref == NULL)
                    continue;

                // Diamond prune is for refops not in the same BB
                if (incref->getParent() == decref->getParent())
                    continue;

                // If the refops are unrelated, skip
                if (!isRelatedDecref(incref, decref))
                    continue;

                // incref DOM decref && decref POSTDOM incref
                if (DT.dominates(incref, decref) &&
                    PDT.dominates(decref, incref)) {
                    // check that the decref cannot be executed multiple times
                    SmallBBSet tail_nodes;
                    tail_nodes.insert(decref->getParent());
                    if (!verifyFanoutBackward(incref, incref->getParent(),
                                              &tail_nodes, false))

                        continue;

                    // scan the CFG between the incref and decref BBs, if
                    // there's a decref present then skip, this is conservative.
                    if (hasDecrefBetweenGraph(incref->getParent(),
                                              decref->getParent())) {
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

    /**
     * "Fan-out" pruning passes.
     *
     * Prunes "fan-out"s, this is where control flow from a block containing an
     * incref "fans out" into blocks that contain corresponding decrefs.
     *
     * There are two supported fan-out shape CFG structures.
     *
     * Supported case 1, simple "fan-out" with no raise, prune occurs when the
     * incref dominates the predecessor blocks containing associated decrefs.
     *
     *           ┌────────────┐
     *           │ incref (A) │
     *           └────────────┘
     *             /        \
     *            /          \
     *           /            \
     *          .              .
     *          .              .
     *   ┌────────────┐ ┌────────────┐
     *   │ MORE CFG   │ │ MORE CFG   │
     *   └────────────┘ └────────────┘
     *          .              .
     *          .              .
     *   ┌────────────┐ ┌────────────┐
     *   │ decref (A) │ │ decref (A) │
     *   └────────────┘ └────────────┘
     *          .              .
     *          .              .
     *          .              .
     *
     *
     * Supported case 2, simple "fan-out" with raise, prune occurs when the
     * incref dominates the predecessor blocks containing associated decrefs
     * with the exception of the raise block (this is to "forgive" the
     * occasional missing decref in a raise block).
     *
     *           ┌────────────┐
     *           │ incref (A) │
     *           └────────────┘
     *             /        \
     *            /          \
     *           /            \
     *          .              .
     *          .              .
     *   ┌────────────┐ ┌────────────┐
     *   │ MORE CFG   │ │ MORE CFG   │
     *   └────────────┘ └────────────┘
     *          .              .
     *          .              .
     *   ┌────────────┐ ┌────────────┐
     *   │ decref (A) │ │ raise      │
     *   └────────────┘ └────────────┘
     *          .
     *          .
     *   ┌────────────┐
     *   │ MORE CFG   │
     *   └────────────┘
     *
     * a complex pattern about fanout-raise
     * https://github.com/numba/llvmlite/issues/1023
     *           ┌────────────┐
     *           │   incref   │
     *           │   incref   │
     *           └────────────┘
     *             /           \
     *            /             \
     *     ┌────────────┐        \
     *     │   decref   |         \
     *     └────────────┘          \
     *      /          \            \
     *     /            \            \
     * ┌────────────┐ ┌────────────┐  \
     * │   decref   | │   incref   |   \
     * └────────────┘ └────────────┘    \
     *                 /            \    \
     *                /              \    \
     *           ┌────────────┐      ┌────────────┐
     *           │   decref   |      │   raise    |
     *           │   decref   |      └────────────┘
     *           └────────────┘
     *
     * Parameters:
     *  - F a Function
     *  - prune_raise_exit, if false case 1 is considered, if true case 2 is
     *    considered.
     *
     * Returns:
     *  - true if pruning took place, false otherwise
     */
    bool runFanoutPrune(Function &F, bool prune_raise_exit) {
        bool mutated = false;

        // Find all Increfs and store them in incref_list
        std::vector<CallInst *> incref_list;
        listRefOps(F, IsIncRef, incref_list);

        // Remember incref-blocks that will always fail.
        SmallBBSet bad_blocks;
        // walk the incref_list
        for (CallInst *incref : incref_list) {
            // Skip blocks that will always fail.
            if (bad_blocks.count(incref->getParent())) {
                continue; // skip
            }

            // Is there *any* decref in the parent node of the incref?
            // If so skip this incref (considering that aliases may exist).
            if (hasAnyDecrefInNode(incref->getParent())) {
                // be careful of potential alias
                continue; // skip
            }

            SmallBBSet decref_blocks;
            // Check for the chosen "fan out" condition
            if (findFanout(incref, bad_blocks, &decref_blocks,
                           prune_raise_exit)) {
                if (DEBUG_PRINT) {
                    F.viewCFG();
                    errs() << "------------\n";
                    errs() << "incref " << incref->getParent()->getName()
                           << "\n";
                    errs() << "  decref_blocks.size()" << decref_blocks.size()
                           << "\n";
                    incref->dump();
                }
                // Remove first related decref in each block
                // for each block
                for (BasicBlock *each : decref_blocks) {
                    // for each instruction
                    for (Instruction &ii : *each) {
                        CallInst *decref;
                        // walrus:
                        // is the current instruction the decref associated with
                        // the incref under consideration, if so assign to
                        // decref and continue.
                        if ((decref = isRelatedDecref(incref, &ii))) {
                            if (DEBUG_PRINT) {
                                errs()
                                    << decref->getParent()->getName() << "\n";
                                decref->dump();
                            }
                            // Remove this decref from its block
                            decref->eraseFromParent();

                            // update counters based on decref removal
                            if (prune_raise_exit)
                                stats_fanout_raise += 1;
                            else
                                stats_fanout += 1;
                            break;
                        }
                    }
                }
                // remove the incref from its block
                incref->eraseFromParent();

                // update counters based on incref removal
                if (prune_raise_exit)
                    stats_fanout_raise += 1;
                else
                    stats_fanout += 1;
                mutated = true;
            }
        }
        return mutated;
    }

    /**
     * This searches for the "fan-out" condition and returns true if it is
     * found.
     *
     * Parameters:
     * - incref: the incref from which fan-out should be checked.
     * - bad_blocks: a set of blocks that are known to not satisfy the
     *   the fanout condition. Mutated by this function.
     * - decref_blocks: pointer to a set of basic blocks, this is mutated by
     *   this function, on return it contains the basic blocks containing
     *   decrefs related to the incref
     * - prune_raise_exit: this is a bool to signal whether to just look for
     *   the fan-out case or also look for the fan-out with raise condition,
     *   if true the fan-out with raise condition is considered else it is
     *   not.
     *
     * Returns:
     *  - true if the fan-out condition specified by `prune_raise_exit` was
     *    found, false otherwise.
     */
    bool findFanout(CallInst *incref, SmallBBSet &bad_blocks,
                    SmallBBSet *decref_blocks, bool prune_raise_exit) {

        // get the basic block of the incref instruction
        BasicBlock *head_node = incref->getParent();

        // work space, a set of basic blocks to hold the block which contain
        // raises, only used in the case of prune_raise_exit
        SmallBBSet raising_blocks, *p_raising_blocks = NULL;
        // Set up pointer to raising_blocks
        if (prune_raise_exit)
            p_raising_blocks = &raising_blocks;

        if (findFanoutDecrefCandidates(incref, head_node, bad_blocks,
                                       decref_blocks, p_raising_blocks)) {
            if (DEBUG_PRINT) {
                errs() << "forward pass candids.size() = "
                       << decref_blocks->size() << "\n";
                errs() << "    " << head_node->getName() << "\n";
                incref->dump();
            }
            if (decref_blocks->size() == 0) {
                // no decref blocks
                if (DEBUG_PRINT) {
                    errs() << "missing decref blocks = "
                           << raising_blocks.size() << "\n";
                }
                return false;
            }
            if (prune_raise_exit) {
                if (raising_blocks.size() == 0) {
                    // no raising blocks
                    if (DEBUG_PRINT) {
                        errs() << "missing raising blocks = "
                               << raising_blocks.size() << "\n";
                        for (auto bb : *decref_blocks) {
                            errs() << "   " << bb->getName() << "\n";
                        }
                    }
                    return false;
                }

                // combine decref_blocks into raising blocks for checking the
                // exit node condition
                for (BasicBlock *bb : *decref_blocks) {
                    raising_blocks.insert(bb);
                }
                if (verifyFanoutBackward(incref, head_node, p_raising_blocks,
                                         prune_raise_exit))
                    return true;

            } else if (verifyFanoutBackward(incref, head_node, decref_blocks,
                                            prune_raise_exit)) {
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
     *
     * In the case of a decref node, the node is added to decref_blocks only if
     * it contains a decref associated with the incref and there is no interior
     * back-edge to a predecessor in the current sub-graph.
     *
     * In the case of an exit, it must be a raise for it to be added to
     * raising_blocks.
     *
     * Parameters:
     *  - incref: The incref under consideration.
     *  - cur_node: The basic block in which incref is found.
     *  - bad_blocks: a set of blocks that are known to not satisfy the
     *    the fanout condition. Mutated by this function.
     *  - decref_blocks: pointer to a set of basic blocks, it is mutated by this
     *    function and on successful return contains the basic blocks which have
     *    a decref related to the supplied incref in them.
     *  - raising_blocks: point to a set of basic blocks OR NULL. If not-NULL
     *    it is mutated by this function and on successful return contains the
     *    basic blocks which have a raise in them that is reachable from the
     *    incref.
     *
     * Return condition:
     *   depends on the value of raising_blocks:
     *      == NULL -> return true iff all paths from the incref have led to a
     *                 decref.
     *      != NULL -> return true iff all paths from the incref have led to
     *                 either a decref or a raising exit.
     */
    bool findFanoutDecrefCandidates(CallInst *incref, BasicBlock *cur_node,
                                    SmallBBSet &bad_blocks,
                                    SmallBBSet *decref_blocks,
                                    SmallBBSet *raising_blocks) {
        // stack of basic blocks for the walked path(s)
        SmallVector<BasicBlock *, FANOUT_RECURSE_DEPTH> path_stack;
        bool found = false;
        // Get the terminator of the basic block containing the incref, the
        // search starts from here.
        auto term = cur_node->getTerminator();

        // RAII push cur_node onto the work stack
        raiiStack<SmallVectorImpl<BasicBlock *>> raii_path_stack(path_stack,
                                                                 cur_node);

        // This is a pass-by-ref accumulator.
        unsigned subgraph_size = 0;

        // Walk the successors of the terminator.
        for (unsigned i = 0; i < term->getNumSuccessors(); ++i) {
            // Get the successor
            BasicBlock *child = term->getSuccessor(i);
            // Walk the successor looking for decrefs
            found =
                walkChildForDecref(incref, child, path_stack, subgraph_size,
                                   bad_blocks, decref_blocks, raising_blocks);
            // if not found, return false
            if (!found)
                return found; // found must be false
        }
        return found;
    }

    /**
     * "Walk" a child node looking for blocks containing decrefs or raises that
     *  meet the conditions described in findFanoutDecrefCandidates.
     *
     * Parameters:
     * - incref: The incref under consideration
     * - cur_node: The current basic block being assessed
     * - path_stack: A stack of basic blocks representing unsearched paths
     * - bad_blocks: a set of blocks that are known to not satisfy the
     *   the fanout condition. Mutated by this function.
     * - subgraph_size: accumulator to count the subgraph size (node count).
     * - decref_blocks: a set that stores references to accepted blocks that
     *   contain decrefs associated with the incref.
     * - raising_blocks: a set that stores references to accepted blocks that
     *   contain raises.
     *
     * Returns:
     *  - true if the conditions above hold, false otherwise.
     */
    bool walkChildForDecref(CallInst *incref, BasicBlock *cur_node,
                            SmallVectorImpl<BasicBlock *> &path_stack,
                            unsigned &subgraph_size, SmallBBSet &bad_blocks,
                            SmallBBSet *decref_blocks,
                            SmallBBSet *raising_blocks) {
        // If the current path stack exceeds the recursion depth, stop, return
        // false.
        if (path_stack.size() >= FANOUT_RECURSE_DEPTH)
            return false;

        // Reject subgraph that is bigger than the subgraph_limit
        if (++subgraph_size > subgraph_limit) {
            // mark head-node as always fail because that subgraph is too big
            // to analyze.
            bad_blocks.insert(incref->getParent());
            return false;
        }

        // Check for the back-edge condition...
        // If the current block is in the path stack
        if (basicBlockInList(cur_node, path_stack)) {
            // If the current node is TOS
            if (cur_node == path_stack[0]) {
                // Reject interior node back-edge to start of sub-graph.
                // This means that the incref can be executed multiple times
                // before reaching the decref.

                // mark head-node as always fail.
                bad_blocks.insert(incref->getParent());
                return false;
            }
            // it is a legal backedge; skip
            return true;
        }

        // Does the current block have a related decref?
        if (hasDecrefInNode(incref, cur_node)) {
            // Add to the list of decref_blocks
            decref_blocks->insert(cur_node);
            return true; // done for this path
        }

        // Are there any decrefs in the current node?
        if (hasAnyDecrefInNode(cur_node)) {
            // Because we don't know about aliasing

            // mark head-node as always fail.
            bad_blocks.insert(incref->getParent());
            return false;
        }

        // If raising_blocks is non-NULL, see if the current node is a block
        // which raises, if so add to the raising_blocks list, this path is now
        // finished.
        if (raising_blocks && isRaising(cur_node)) {
            raising_blocks->insert(cur_node);
            return true; // done for this path
        }

        // Continue searching by recursing into successors of the current
        // block.

        // First RAII push cur_node as TOS
        raiiStack<SmallVectorImpl<BasicBlock *>> raii_push_pop(path_stack,
                                                               cur_node);
        bool found = false;
        // get cur_node terminator
        auto term = cur_node->getTerminator();
        // walk successors of the current node
        for (unsigned i = 0; i < term->getNumSuccessors(); ++i) {
            // get a successor
            BasicBlock *child = term->getSuccessor(i);
            // recurse
            found =
                walkChildForDecref(incref, child, path_stack, subgraph_size,
                                   bad_blocks, decref_blocks, raising_blocks);
            if (!found)
                return false;
        }
        // If this is a leaf node, returns false.
        return found;
    }

    /**
     * Backward pass.
     * Check the tail-node condition for the fanout subgraph:
     * The reverse walks from all exit-nodes must end with the head-node
     * and the tail-nodes cannot be executed multiple times.
     *
     * Parameters:
     * - incref: the incref instruction
     * - head_node: the basic block containing the arg incref
     * - tail_nodes: a set containing the basic block(s) in which decrefs
     *   corresponding to the arg incref instruction exist.
     *
     * Returns:
     * - true if it could be verified that there's no loop structure
     *   surrounding the use of the decrefs, false else.
     *
     */
    bool verifyFanoutBackward(CallInst *incref, BasicBlock *head_node,
                              const SmallBBSet *tail_nodes,
                              bool prune_raise_exit) {
        // push the tail nodes into a work list
        SmallVector<BasicBlock *, 10> todo;
        for (BasicBlock *bb : *tail_nodes) {
            todo.push_back(bb);
        }

        // visited is for bookkeeping to hold reference to those nodes which
        // have already been visited.
        SmallBBSet visited;
        // while there is work...
        while (todo.size() > 0) {
            SmallVector<BasicBlock *, FANOUT_RECURSE_DEPTH> workstack;
            // pop an element from the work list into the work stack
            workstack.push_back(todo.pop_back_val());

            // while there's work on the local workstack
            while (workstack.size() > 0) {
                // Get a basic block
                BasicBlock *cur_node = workstack.pop_back_val();
                // If cur_node is a raising block, then skip it
                if (prune_raise_exit && isRaising(cur_node)) {
                    continue;
                }
                // if the block has been seen before then skip
                if (visited.count(cur_node)) {
                    // Already visited
                    continue; // skip
                }

                if (cur_node == &head_node->getParent()->getEntryBlock()) {
                    // Arrived at the entry node of the function.
                    // This means the reverse walk from a tail-node can
                    // bypass the head-node (incref node) of this fanout
                    // subgraph.
                    return false;
                }

                // remember that we have visited this node already
                visited.insert(cur_node);

                // Walk into all predecessors
                // pred_begin and pred_end are defined under Functions in:
                // http://llvm.org/doxygen/IR_2CFG_8h.html
                auto it = pred_begin(cur_node), end = pred_end(cur_node);
                for (; it != end; ++it) {
                    auto pred = *it;
                    if (tail_nodes->count(pred)) {
                        // reject because a predecessor is a block containing
                        // a decref matching the incref
                        return false;
                    }
                    if (pred != head_node) {
                        // If the predecessor is the head-node,
                        // this path is ok; otherwise, continue to walk up.
                        workstack.push_back(pred);
                    }
                }
            }
        }
        // analysis didn't exit, all conditions must be ok, return true
        return true;
    }

    /**
     * Check if a basic block is a block which raises, based on writing to the
     * `%excinfo`.
     *
     * Parameters:
     *  - bb a basic block
     *
     * Returns:
     *  - true if basic block bb contains a raise with the appropriate metadata,
     *    false otherwise
     */
    bool isRaising(const BasicBlock *bb) {
        for (auto &instruction : *bb) {
            if (instruction.getOpcode() == Instruction::Store) {
                auto name = dyn_cast<StoreInst>(&instruction)
                                ->getPointerOperand()
                                ->getName();
                if (name.compare("excinfo") == 0 &&
                    instruction.hasMetadata("numba_exception_output")) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Does "Is a basic block in a given list"
     *
     * Template parameter <T>:
     *  - the type of list
     *
     * Parameters:
     *  - bb  a basic block
     *  - list a list-like container in which to search
     *
     * Returns:
     *  - true if bb is in list, false else.
     */
    template <class T>
    bool basicBlockInList(const BasicBlock *bb, const T &list) {
        for (BasicBlock *each : list) {
            if (bb == each)
                return true;
        }
        return false;
    }

    /**
     * Check to see if a basic block contains a decref related to a given incref
     *
     * Parameters:
     *  - incref an incref
     *  - bb  a basic block
     *
     * Returns:
     *  - true if basic block bb contains a decref related to incref, false
     *    otherwise.
     */
    bool hasDecrefInNode(CallInst *incref, BasicBlock *bb) {
        for (Instruction &ii : *bb) {
            if (isRelatedDecref(incref, &ii) != NULL) {
                return true;
            }
        }
        return false;
    }

    /**
     * Checks if an instruction is a decref that is related to the given incref.
     *
     * Parameters:
     *  - incref an incref
     *  - bb  a basic block
     *
     * Returns:
     *  - returns input ii as a CallInst* if it is a decref related to incref,
     *    NULL otherwise.
     */
    CallInst *isRelatedDecref(CallInst *incref, Instruction *ii) {
        CallInst *suspect;
        if ((suspect = GetRefOpCall(ii))) {
            if (!IsDecRef(suspect)) {
                return NULL;
            }
            if (incref->getArgOperand(0) != suspect->getArgOperand(0)) {
                return NULL;
            }
            return suspect;
        }
        return NULL;
    }

    /**
     * Checks if the first argument to the supplied call_inst is NULL and
     * returns true if so, false otherwise.
     *
     * Parameters:
     *  - call_inst, a call instruction to check.
     *
     * Returns:
     *  - true is the first argument to call_inst is not NULL, false otherwise
     */
    bool isNonNullFirstArg(CallInst *call_inst) {
        auto val = call_inst->getArgOperand(0);
        auto ptr = dyn_cast<ConstantPointerNull>(val);
        return ptr == NULL;
    }

    /**
     * Scans a basic block for decrefs and returns true if one is found,
     *  false otherwise
     *
     * Parameters:
     *  - bb, a basic block
     *
     * Returns:
     *  - true if there is a decref in the basic block, false otherwise.
     */
    bool hasAnyDecrefInNode(BasicBlock *bb) {
        for (Instruction &ii : *bb) {
            CallInst *refop = GetRefOpCall(&ii);
            if (refop != NULL && IsDecRef(refop)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Determines if there is a decref between two nodes in a graph.
     *
     * NOTE: Required condition: head_node dominates tail_node
     *
     * Parameters:
     *  - head_node, a basic block which is the head of the graph
     *  - tail_node, a basic block which is the tail of the graph
     *
     * Returns:
     *  - true if there is a decref, false else
     *
     */
    bool hasDecrefBetweenGraph(BasicBlock *head_node, BasicBlock *tail_node) {
        // This function implements a depth-first search.

        // visited keeps track of the visited blocks
        SmallBBSet visited;
        // stack keeps track of blocks to be checked.
        SmallVector<BasicBlock *, 20> stack;
        // start with the head_node;
        stack.push_back(head_node);
        do {
            BasicBlock *cur_node = stack.pop_back_val();
            // First, is the current BB already visited, if so return false,
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
            if (hasAnyDecrefInNode(cur_node))
                return true;

            // get the terminator of the current node
            Instruction *term = cur_node->getTerminator();
            // walk the successor blocks
            for (unsigned i = 0; i < term->getNumSuccessors(); ++i) {
                BasicBlock *child = term->getSuccessor(i);
                // if the successor is the tail node, skip
                if (child == tail_node)
                    continue;
                // else check the subgraph between the current successor and the
                // tail
                stack.push_back(child);
            }
        } while (stack.size() > 0);
        return false;
    }

    typedef bool (*test_refops_function)(CallInst *);

    /**
     * Walks the basic blocks of a function F, scans each instruction, if the
     * instruction is a refop and calling `test_refops_function` on it evaluates
     * to true then add it to list.
     *
     * Templates Parameter <T>
     *  - the type of list
     *
     * Parameters:
     * - F a LLVM function
     * - test_refops_function a function that takes an Instruction instance and
     *   returns true if the instance is a refop, false otherwise
     * - list, a list-like container to hold reference to instruction instances
     *   which are identified by test_refops_function.
     */
    template <class T>
    void listRefOps(Function &F, test_refops_function fn, T &list) {
        // For each basic block in the function
        for (BasicBlock &bb : F) {
            // For each instruction the basic block
            for (Instruction &ii : bb) {
                CallInst *ci;
                // if the instruction is a refop
                if ((ci = GetRefOpCall(&ii))) {
                    // and the test_refops_function returns true when called
                    // on the instruction
                    if (fn(ci)) {
                        // add to the list
                        list.push_back(ci);
                    }
                }
            }
        }
    }
}; // end of struct RefPrune

} // namespace

class RefPrunePass : public PassInfoMixin<RefPrunePass> {

  public:
    Subpasses flags;
    size_t subgraph_limit;
    RefPrunePass(Subpasses flags = Subpasses::All, size_t subgraph_limit = -1)
        : flags(flags), subgraph_limit(subgraph_limit) {}

    PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
        auto &DT = AM.getResult<DominatorTreeAnalysis>(F);
        auto &PDT = AM.getResult<PostDominatorTreeAnalysis>(F);
        if (RefPrune(DT, PDT, flags, subgraph_limit).runOnFunction(F)) {
            return PreservedAnalyses::none();
        }

        return PreservedAnalyses::all();
    }
};

class RefNormalizePass : public PassInfoMixin<RefNormalizePass> {

  public:
    RefNormalizePass() = default;

    PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
        if (RefNormalize().runOnFunction(F)) {
            return PreservedAnalyses::none();
        }

        return PreservedAnalyses::all();
    }
};

size_t RefPrune::stats_per_bb = 0;
size_t RefPrune::stats_diamond = 0;
size_t RefPrune::stats_fanout = 0;
size_t RefPrune::stats_fanout_raise = 0;

extern "C" {

API_EXPORT(void)
LLVMPY_AddRefPrunePass_module(LLVMModulePassManagerRef MPM, int subpasses,
                              size_t subgraph_limit) {
    llvm::unwrap(MPM)->addPass(
        createModuleToFunctionPassAdaptor(RefNormalizePass()));
    llvm::unwrap(MPM)->addPass(createModuleToFunctionPassAdaptor(
        RefPrunePass((Subpasses)subpasses, subgraph_limit)));
}

API_EXPORT(void)
LLVMPY_AddRefPrunePass_function(LLVMFunctionPassManagerRef FPM, int subpasses,
                                size_t subgraph_limit) {
    llvm::unwrap(FPM)->addPass(RefNormalizePass());
    llvm::unwrap(FPM)->addPass(
        RefPrunePass((Subpasses)subpasses, subgraph_limit));
}

/**
 * Struct for holding statistics about the amount of pruning performed by
 * each type of pruning algorithm.
 */
typedef struct PruneStats {
    size_t basicblock;
    size_t diamond;
    size_t fanout;
    size_t fanout_raise;
} PRUNESTATS;

API_EXPORT(void)
LLVMPY_DumpRefPruneStats(PRUNESTATS *buf, bool do_print) {
    /* PRUNESTATS is updated with the statistics about what has been pruned from
     * the RefPrune static state vars. This isn't threadsafe but neither is
     * the LLVM pass infrastructure so it's all done under a python thread lock.
     *
     * do_print if set will print the stats to stderr.
     */
    if (do_print) {
        errs() << "refprune stats "
               << "per-BB " << RefPrune::stats_per_bb << " "
               << "diamond " << RefPrune::stats_diamond << " "
               << "fanout " << RefPrune::stats_fanout << " "
               << "fanout+raise " << RefPrune::stats_fanout_raise << " "
               << "\n";
    };

    buf->basicblock = RefPrune::stats_per_bb;
    buf->diamond = RefPrune::stats_diamond;
    buf->fanout = RefPrune::stats_fanout;
    buf->fanout_raise = RefPrune::stats_fanout_raise;
}

} // extern "C"
