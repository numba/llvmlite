#include "llvm-c/BitReader.h"
#include "llvm-c/BitWriter.h"

#include "core.h"


extern "C" {

API_EXPORT(void)
LLVMPY_WriteBitcodeToString(LLVMModuleRef M,
                            const char **outbuf, size_t *outlen)
{
    LLVMMemoryBufferRef MB = LLVMWriteBitcodeToMemoryBuffer(M);
    *outlen = LLVMGetBufferSize(MB);
    *outbuf = LLVMPY_CreateByteString(LLVMGetBufferStart(MB), *outlen);
    LLVMDisposeMemoryBuffer(MB);
}

API_EXPORT(LLVMModuleRef)
LLVMPY_ParseBitcode(LLVMContextRef context,
                    const char *bitcode, size_t bitcodelen,
                    char **outmsg)
{
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
