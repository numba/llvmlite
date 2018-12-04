#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Demangle/Demangle.h"
#include <memory>

using namespace llvm;

namespace {
    /*
        Sample Hello World function pass. Named pyhello to avoid conflict
        with LLVM's built-in example pass
    */
    struct Hello : public FunctionPass {
        static char ID;
        Hello() : FunctionPass(ID) { }
        bool runOnFunction(Function& F) override {
            errs() << "Hello: ";
            errs().write_escaped(F.getName()) << "\n";
            return false;
        }
    };

    /*
        Safely register a pass, i.e. don't register it if a pass
        with the same name is already registered.
    */
    template<typename T>
    class SafeRegister {
        public:
        SafeRegister(StringRef arg,
                    StringRef name,
                    bool CFGOnly = false,
                    bool is_analysis = false) {
            auto registry = PassRegistry::getPassRegistry();
            // check if there is already a pyhello pass
            auto passInfo = registry->getPassInfo(arg);
            if (passInfo == nullptr) {
                pass_info_ = make_unique<PassInfo>(name, arg, &T::ID,
                    PassInfo::NormalCtor_t(callDefaultCtor<T>), CFGOnly,
                    is_analysis);
                registry->registerPass(*pass_info_);
            }
        }
        private:
        std::unique_ptr<PassInfo> pass_info_;
    };

    char Hello::ID = 0;

    static SafeRegister<Hello> X("pyhello", "Hello World Pass",
                                    false, false);
} // end anonymous