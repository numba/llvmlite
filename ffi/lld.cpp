#include "lld/Common/Driver.h"

int lld_main(int Argc, const char **Argv) {
    //InitLLVM X(Argc, Argv);
    std::vector<const char *> Args(Argv, Argv + Argc);
    return !lld::elf::link(Args, false);
}
