#include <sstream>

#include "core.h"

#include "llvm-c/Transforms/IPO.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm/ADT/STLExtras.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/DiagnosticPrinter.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/ToolOutputFile.h"
#include "llvm/Support/YAMLTraits.h"
#include "llvm/Support/raw_ostream.h"

#include "llvm-c/Transforms/IPO.h"
#include "llvm-c/Transforms/Scalar.h"
#include "llvm/IR/LLVMRemarkStreamer.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Remarks/RemarkStreamer.h"
#include "llvm/Transforms/IPO.h"
#include "llvm/Transforms/Scalar.h"

#include <llvm/IR/PassTimingInfo.h>

#include <llvm/Analysis/AliasAnalysisEvaluator.h>
#include <llvm/Analysis/BasicAliasAnalysis.h>
#include <llvm/Analysis/CFGPrinter.h>
#include <llvm/Analysis/CallPrinter.h>
#include <llvm/Analysis/DependenceAnalysis.h>
#include <llvm/Analysis/DomPrinter.h>
#include <llvm/Analysis/GlobalsModRef.h>
#include <llvm/Analysis/IVUsers.h>
#include <llvm/Analysis/Lint.h>
#include <llvm/Analysis/Passes.h>
#include <llvm/Analysis/ScalarEvolutionAliasAnalysis.h>
#include <llvm/CodeGen/Passes.h>
#include <llvm/Transforms/AggressiveInstCombine/AggressiveInstCombine.h>
#include <llvm/Transforms/IPO.h>
#include <llvm/Transforms/IPO/AlwaysInliner.h>
#include <llvm/Transforms/Scalar/SimpleLoopUnswitch.h>
#include <llvm/Transforms/Utils.h>
#include <llvm/Transforms/Utils/UnifyFunctionExitNodes.h>
using namespace llvm;

/*
 * Exposed API
 */

extern "C" {

API_EXPORT(void)
LLVMPY_SetTimePasses(bool enable) { TimePassesIsEnabled = enable; }

API_EXPORT(void)
LLVMPY_ReportAndResetTimings(const char **outmsg) {
    std::string osbuf;
    raw_string_ostream os(osbuf);
    reportAndResetTimings(&os);
    os.flush();
    *outmsg = LLVMPY_CreateString(os.str().c_str());
}

} // end extern "C"
