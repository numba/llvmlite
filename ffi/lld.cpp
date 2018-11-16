#include "lld/Common/Driver.h"

extern "C" {

int lld_main(int Argc, const char **Argv) {
    //InitLLVM X(Argc, Argv);
    std::vector<const char *> Args(Argv, Argv + Argc);
    return !lld::elf::link(Args, false);
}

int lld_main_help() {
    std::vector<const char *> Args = {"ld.lld", "--help"};
    return !lld::elf::link(Args, false);
}

int lld_main_2(const char *a, const char *b) {
    std::vector<const char *> Args = {a, b};
    return !lld::elf::link(Args, false);
}

} // end extern "C"
