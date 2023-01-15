#include "core.h"
#include "lld/Common/Driver.h"
#include "llvm/Support/raw_ostream.h"

extern "C" {

API_EXPORT(bool) lld_main(int Argc, const char **Argv, const char **outstr) {
    // InitLLVM X(Argc, Argv);
    std::string command_output;
    llvm::raw_string_ostream command_stream(command_output);
    std::vector<const char *> Args(Argv, Argv + Argc);

    bool linker_output =
        !lld::elf::link(Args, false, command_stream, command_stream);

    *outstr = LLVMPY_CreateString(command_output.c_str());
    return linker_output;
}

} // end extern "C"