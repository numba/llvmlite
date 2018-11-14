#include "lld/Common/Driver.h"
#include <cstdlib>

int main_test(int Argc, const char **Argv) {
    //InitLLVM X(Argc, Argv);
    std::vector<const char *> Args(Argv, Argv + Argc);
    return !lld::elf::link(Args, false);
}
