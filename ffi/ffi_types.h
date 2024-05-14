
#pragma once

#include "core.h"

#include "llvm/IR/PassManager.h"
#include "llvm/IR/PassTimingInfo.h"
#include "llvm/Passes/PassBuilder.h"

typedef llvm::PassBuilder *LLVMPassBuilder;

typedef llvm::FunctionPassManager *LLVMFunctionPassManager;

typedef llvm::ModulePassManager *LLVMModulePassManager;

typedef llvm::FunctionAnalysisManager *LLVMFunctionAnalysisManager;

typedef llvm::ModuleAnalysisManager *LLVMModuleAnalysisManager;

typedef llvm::CGSCCAnalysisManager *LLVMCGSCCAnalysisManager;

typedef llvm::LoopAnalysisManager *LLVMLoopAnalysisManager;

typedef llvm::PassInstrumentationCallbacks *LLVMPassInstrumentationCallbacks;

typedef llvm::TimePassesHandler *LLVMTimePassesHandler;

typedef llvm::OptimizationLevel const *LLVMOptimizationLevel;
