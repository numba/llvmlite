#include "lld/Common/Driver.h"

int lld_main(int Argc, const char **Argv) {
    //InitLLVM X(Argc, Argv);
    std::vector<const char *> Args(Argv, Argv + Argc);
    return !lld::elf::link(Args, false);
}

int lld_main_help() {
    std::vector<const char *> Args = {"ld.lld", "--help"};
    return !lld::elf::link(Args, false);
}
