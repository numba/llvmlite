#ifndef LLVMPY_CORE_H_
#define LLVMPY_CORE_H_

#include "llvm-c/Core.h"
#include <cstring>
#include <cstdlib>

extern "C" {

const char *
LLVMPY_CreateString(const char *msg);

void
LLVMPY_DisposeString(const char *msg);


LLVMContextRef
LLVMPY_GetGlobalContext();


} /* end extern "C" */


#endif /* LLVMPY_CORE_H_ */
