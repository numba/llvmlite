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
struct PyHello : public FunctionPass {
    static char ID;
    static const std::string name;
    static const std::string arg;
    PyHello() : FunctionPass(ID) { }
    bool runOnFunction(Function& F) override {
        errs() << "Hello: ";
        errs().write_escaped(F.getName()) << "\n";
        return false;
    }
};

char PyHello::ID = 0;
const std::string PyHello::name = "Hello World Pass";
const std::string PyHello::arg = "pyhello";
} // end anonymous

 extern "C" {
#if defined(_MSC_VER)
#define API_EXPORT(RTYPE) __declspec(dllexport) RTYPE
#else
#define API_EXPORT(RTYPE) RTYPE
#endif

API_EXPORT(void) LLVMPY_RegisterPass(LLVMPassRegistryRef PR) {
    auto registry = unwrap(PR);
    // check if there is already a pyhello pass
    auto passInfo = registry->getPassInfo(PyHello::arg);
    if (passInfo == nullptr) {
        passInfo = new PassInfo(PyHello::name, PyHello::arg, &PyHello::ID,
                                PassInfo::NormalCtor_t(callDefaultCtor<PyHello>), false,
                                false);
        registry->registerPass(*passInfo, true);
    }
}
} // end extern "C"
