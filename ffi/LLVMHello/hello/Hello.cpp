#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Demangle/Demangle.h"

using namespace llvm;

namespace {
    struct Hello : public FunctionPass {
        static char ID;
        Hello() : FunctionPass(ID) { }
        bool runOnFunction(Function& F) override {
            char buf[50];
            const auto& mangled = F.getName();
            int status;
            size_t size;
            char* demangled = itaniumDemangle(mangled.str().c_str(), buf, &size, &status);
            errs() << "Hello: ";
            errs().write_escaped(F.getName()) << "\n";
            return false;
        }
    };

    char Hello::ID = 0;

    static RegisterPass<Hello> X("hello", "Hello World Pass",
                                false,
                                false);
} // end anonymous