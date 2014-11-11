#include "llvm-c/BitReader.h"
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

API_EXPORT(LLVMModuleRef)
LLVMPY_ParseBitcode(LLVMContextRef context,
                    const char *bitcode, size_t bitcodelen,
                    char **outmsg)
{
    using namespace llvm;
    LLVMModuleRef ref;
    LLVMMemoryBufferRef mem = LLVMCreateMemoryBufferWithMemoryRange(
        bitcode, bitcodelen,
        "" /* BufferName*/,
        0 /* RequiresNullTerminator*/
    );

    LLVMParseBitcodeInContext(context, mem, &ref, outmsg);
    LLVMDisposeMemoryBuffer(mem);
    return ref;
}

} // end extern "C"
