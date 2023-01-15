#include "core.h"
#include "lld/Common/Driver.h"
#include "llvm/Support/raw_ostream.h"

extern "C" {

API_EXPORT(bool) lld_main(int Argc, const char **Argv, const char **outstr) {
    // InitLLVM X(Argc, Argv);
    std::string command_output;
    llvm::raw_string_ostream command_stream(command_output);
    std::vector<const char *> Args(Argv, Argv + Argc);

#if defined __linux__ || __unix__
    // command output needs to be inverted on linux for some reason
    bool linker_output =
        !lld::elf::link(Args, false, command_stream, command_stream);
#elif defined(WIN32) || defined(_WIN32) || defined(__WIN32__)
    bool linker_output =
        lld::coff::link(Args, false, command_stream, command_stream);
#else
    bool linker_output =
        lld::macho::link(Args, false, command_stream, command_stream);
#endif

    *outstr = LLVMPY_CreateString(command_output.c_str());
    return linker_output;
}

} // end extern "C"