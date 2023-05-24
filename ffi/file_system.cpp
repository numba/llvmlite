#include "core.h"

#include "llvm-c/ExecutionEngine.h"
#include "llvm-c/Object.h"

#include "llvm/Object/ObjectFile.h"
#include "llvm/Support/FileSystem.h"

#include <stdio.h>

extern "C" {

API_EXPORT(uint64_t)
LLVMPY_GetDeviceForFile(const char *path)
{
  llvm::sys::fs::UniqueID ID;
  llvm::sys::fs::getUniqueID(path, ID);
  return ID.getDevice();
}

API_EXPORT(uint64_t)
LLVMPY_GetFileIdForFile(const char *path)
{
  llvm::sys::fs::UniqueID ID;
  llvm::sys::fs::getUniqueID(path, ID);
  return ID.getFile();
}

} // end extern C
