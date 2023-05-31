===========
File system
===========

.. currentmodule:: llvmlite.binding

.. function:: getDeviceForFile(path)

   Gets the llvm::sys::fs::UniqueID associated with the given file path
   and then returns the device associated with that path through a call to
   LLVM's getDevice method on that UniqueID.

.. function:: getFileIdForFile(path)

   Gets the llvm::sys::fs::UniqueID associated with the given file path
   and then returns the file ID associated with that path through a call to
   LLVM's getFile method on that UniqueID.
