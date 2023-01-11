#include "lld/Common/Driver.h"
#include "llvm/Support/raw_ostream.h"

extern "C" {

bool lld_main(int Argc, const char **Argv) {
    //InitLLVM X(Argc, Argv);
    llvm::raw_ostream &output = llvm::outs();
    std::vector<const char *> Args(Argv, Argv + Argc);
    return !lld::elf::link(Args, false, output, output);
}

} // end extern "C"
