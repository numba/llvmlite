#include "llvm/IR/Module.h"
#include "llvm/Bitcode/ReaderWriter.h"
#include "llvm/Support/raw_ostream.h"

#include "core.h"

#include <string>
#include <cstdio>


extern "C" {

API_EXPORT(void)
LLVMPY_WriteBitcodeToString(LLVMModuleRef M,
                            const char **outbuf, size_t *outlen)
{
    using namespace llvm;
    std::string buf;
    raw_string_ostream os(buf);
    WriteBitcodeToFile(unwrap(M), os);
    os.flush();
    *outbuf = LLVMPY_CreateByteString(buf.c_str(), buf.size());
    *outlen = buf.size();
}


} // end extern "C"
