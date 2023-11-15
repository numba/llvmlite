//===---- memorymanager.cpp - Memory manager for MCJIT/RtDyld *- C++ -*----===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// This file implements the section-based memory manager used by the MCJIT
// execution engine and RuntimeDyld
//
//===----------------------------------------------------------------------===//

#include "memorymanager.h"
#include "llvm/Support/MathExtras.h"
#include "llvm/Support/Process.h"

#define DEBUG_TYPE "llvmlite-memory-manager"

namespace llvm {

uint8_t *LlvmliteMemoryManager::allocateDataSection(uintptr_t Size,
                                                    unsigned Alignment,
                                                    unsigned SectionID,
                                                    StringRef SectionName,
                                                    bool IsReadOnly) {
    if (IsReadOnly)
        return allocateSection(LlvmliteMemoryManager::AllocationPurpose::ROData,
                               Size, Alignment);
    return allocateSection(LlvmliteMemoryManager::AllocationPurpose::RWData,
                           Size, Alignment);
}

uint8_t *LlvmliteMemoryManager::allocateCodeSection(uintptr_t Size,
                                                    unsigned Alignment,
                                                    unsigned SectionID,
                                                    StringRef SectionName) {
    return allocateSection(LlvmliteMemoryManager::AllocationPurpose::Code, Size,
                           Alignment);
}

uint8_t *LlvmliteMemoryManager::allocateSection(
    LlvmliteMemoryManager::AllocationPurpose Purpose, uintptr_t Size,
    unsigned Alignment) {
    if (!Alignment)
        Alignment = 16;

    LLVM_DEBUG(dbgs() << "Requested size / alignment: "
                      << format_hex(Size, 2, true) << " / " << Alignment
                      << "\n");

    assert(!(Alignment & (Alignment - 1)) &&
           "Alignment must be a power of two.");

    uintptr_t RequiredSize =
        Alignment * ((Size + Alignment - 1) / Alignment + 1);
    uintptr_t Addr = 0;

    LLVM_DEBUG(dbgs() << "Allocating " << format_hex(RequiredSize, 2, true)
                      << " bytes for ");

    MemoryGroup &MemGroup = [&]() -> MemoryGroup & {
        switch (Purpose) {
        case AllocationPurpose::Code:
            LLVM_DEBUG(dbgs() << "CodeMem at ");
            return CodeMem;
        case AllocationPurpose::ROData:
            LLVM_DEBUG(dbgs() << "RODataMem at ");
            return RODataMem;
        case AllocationPurpose::RWData:
            LLVM_DEBUG(dbgs() << "RWDataMem at ");
            return RWDataMem;
        }
        llvm_unreachable("Unknown LlvmliteMemoryManager::AllocationPurpose");
    }();

    // Look in the list of free memory regions and use a block there if one
    // is available.
    for (FreeMemBlock &FreeMB : MemGroup.FreeMem) {
        if (FreeMB.Free.allocatedSize() >= RequiredSize) {
            Addr = (uintptr_t)FreeMB.Free.base();
            uintptr_t EndOfBlock = Addr + FreeMB.Free.allocatedSize();
            // Align the address.
            Addr = (Addr + Alignment - 1) & ~(uintptr_t)(Alignment - 1);

            if (FreeMB.PendingPrefixIndex == (unsigned)-1) {
                // The part of the block we're giving out to the user is now
                // pending
                MemGroup.PendingMem.push_back(
                    sys::MemoryBlock((void *)Addr, Size));

                // Remember this pending block, such that future allocations can
                // just modify it rather than creating a new one
                FreeMB.PendingPrefixIndex = MemGroup.PendingMem.size() - 1;
            } else {
                sys::MemoryBlock &PendingMB =
                    MemGroup.PendingMem[FreeMB.PendingPrefixIndex];
                PendingMB =
                    sys::MemoryBlock(PendingMB.base(),
                                     Addr + Size - (uintptr_t)PendingMB.base());
            }

            // Remember how much free space is now left in this block
            FreeMB.Free = sys::MemoryBlock((void *)(Addr + Size),
                                           EndOfBlock - Addr - Size);
            LLVM_DEBUG(dbgs() << format_hex(Addr, 18, true) << "\n");
            return (uint8_t *)Addr;
        }
    }

    assert(false && "All memory must be pre-allocated");

    return nullptr;
}

static uintptr_t requiredPageSize(uintptr_t Size, uint32_t Alignment) {
    static const size_t PageSize = sys::Process::getPageSizeEstimate();
    // Use the same calculation as allocateSection because we need to be able to
    // satisfy it.
    uintptr_t RequiredSize =
        Alignment * ((Size + Alignment - 1) / Alignment + 1);
    // Round up to the nearest page size. Blocks must be page-aligned.
    return PageSize * ((RequiredSize + PageSize - 1) / PageSize);
}

void LlvmliteMemoryManager::reserveAllocationSpace(
    uintptr_t CodeSize, uint32_t CodeAlign, uintptr_t RODataSize,
    uint32_t RODataAlign, uintptr_t RWDataSize, uint32_t RWDataAlign) {
    MemoryGroup &MemGroup = CodeMem;

    // MemoryManager does not have functions for releasing memory after it's
    // allocated. Normally it tries to use any excess blocks that were
    // allocated due to page alignment, but if we have insufficient free memory
    // for the request this can lead to allocating disparate memory that can
    // violate the ARM ABI. Clear free memory so only the new allocations are
    // used, but do not release allocated memory as it may still be in-use.
    CodeMem.FreeMem.clear();
    RODataMem.FreeMem.clear();
    RWDataMem.FreeMem.clear();

    LLVM_DEBUG(dbgs() << "Code size / align: " << format_hex(CodeSize, 2, true)
                      << " / " << CodeAlign << "\n");
    LLVM_DEBUG(dbgs() << "ROData size / align: "
                      << format_hex(RODataSize, 2, true) << " / " << RODataAlign
                      << "\n");
    LLVM_DEBUG(dbgs() << "RWData size / align: "
                      << format_hex(RWDataSize, 2, true) << " / " << RWDataAlign
                      << "\n");

    // Code alignment needs to be at least the stub alignment - however, we
    // don't have an easy way to get that here so as a workaround, we assume
    // it's 8, which is the largest value I observed across all platforms.
    CodeAlign = CodeAlign ? CodeAlign : 16;
    uint32_t StubAlign = 8;
    CodeAlign = std::max(CodeAlign, StubAlign);

    RODataAlign = RODataAlign ? RODataAlign : 16;
    RWDataAlign = RWDataAlign ? RWDataAlign : 16;
    uintptr_t RequiredCodeSize = requiredPageSize(CodeSize, CodeAlign);
    uintptr_t RequiredRODataSize = requiredPageSize(RODataSize, RODataAlign);
    uintptr_t RequiredRWDataSize = requiredPageSize(RWDataSize, RWDataAlign);
    uint64_t TotalSize =
        RequiredCodeSize + RequiredRODataSize + RequiredRWDataSize;

    LLVM_DEBUG(dbgs() << "Reserving " << format_hex(TotalSize, 2, true)
                      << " bytes\n");

    // FIXME: It would be useful to define a default allocation size (or add
    // it as a constructor parameter) to minimize the number of allocations.
    //
    // FIXME: Initialize the Near member for each memory group to avoid
    // interleaving.
    std::error_code ec;
    sys::MemoryBlock MB = MMapper.allocateMappedMemory(
        AllocationPurpose::Code, TotalSize, &MemGroup.Near,
        sys::Memory::MF_READ | sys::Memory::MF_WRITE, ec);
    if (ec) {
        // FIXME: Add error propagation to the interface.
        assert(false && "Failed to allocate mapped memory");
    }

    // Save this address as the basis for our next request
    MemGroup.Near = MB;

    // Copy the address to all the other groups, if they have not
    // been initialized.
    if (CodeMem.Near.base() == nullptr)
        CodeMem.Near = MB;
    if (RODataMem.Near.base() == nullptr)
        RODataMem.Near = MB;
    if (RWDataMem.Near.base() == nullptr)
        RWDataMem.Near = MB;

    // Remember that we allocated this memory
    MemGroup.AllocatedMem.push_back(MB);

    uintptr_t Addr = (uintptr_t)MB.base();

    FreeMemBlock FreeMB;
    FreeMB.PendingPrefixIndex = (unsigned)-1;

    if (CodeSize > 0) {
        LLVM_DEBUG(dbgs() << "Code mem starts at " << format_hex(Addr, 18, true)
                          << ", size " << format_hex(RequiredCodeSize, 2, true)
                          << "\n");
        FreeMB.Free = sys::MemoryBlock((void *)Addr, RequiredCodeSize);
        CodeMem.FreeMem.push_back(FreeMB);
        Addr += RequiredCodeSize;
    }

    if (RODataSize > 0) {
        LLVM_DEBUG(dbgs() << "Rodata mem starts at 0x"
                          << format_hex(Addr, 18, true) << ", size "
                          << format_hex(RequiredRODataSize, 2, true) << "\n");
        FreeMB.Free = sys::MemoryBlock((void *)Addr, RequiredRODataSize);
        RODataMem.FreeMem.push_back(FreeMB);
        Addr += RequiredRODataSize;
    }

    if (RWDataSize > 0) {
        LLVM_DEBUG(dbgs() << "Rwdata mem starts at 0x"
                          << format_hex(Addr, 18, true) << ", size "
                          << format_hex(RequiredRWDataSize, 2, true) << "\n");
        FreeMB.Free = sys::MemoryBlock((void *)Addr, RequiredRWDataSize);
        RWDataMem.FreeMem.push_back(FreeMB);
    }
}

bool LlvmliteMemoryManager::finalizeMemory(std::string *ErrMsg) {
    // FIXME: Should in-progress permissions be reverted if an error occurs?
    std::error_code ec;

    // Make code memory executable.
    ec = applyMemoryGroupPermissions(CodeMem, sys::Memory::MF_READ |
                                                  sys::Memory::MF_EXEC);
    if (ec) {
        if (ErrMsg) {
            *ErrMsg = ec.message();
        }
        return true;
    }

    // Make read-only data memory read-only.
    ec = applyMemoryGroupPermissions(RODataMem, sys::Memory::MF_READ);
    if (ec) {
        if (ErrMsg) {
            *ErrMsg = ec.message();
        }
        return true;
    }

    // Read-write data memory already has the correct permissions

    // Some platforms with separate data cache and instruction cache require
    // explicit cache flush, otherwise JIT code manipulations (like resolved
    // relocations) will get to the data cache but not to the instruction cache.
    invalidateInstructionCache();

    return false;
}

static sys::MemoryBlock trimBlockToPageSize(sys::MemoryBlock M) {
    static const size_t PageSize = sys::Process::getPageSizeEstimate();

    size_t StartOverlap =
        (PageSize - ((uintptr_t)M.base() % PageSize)) % PageSize;

    size_t TrimmedSize = M.allocatedSize();
    TrimmedSize -= StartOverlap;
    TrimmedSize -= TrimmedSize % PageSize;

    sys::MemoryBlock Trimmed((void *)((uintptr_t)M.base() + StartOverlap),
                             TrimmedSize);

    assert(((uintptr_t)Trimmed.base() % PageSize) == 0);
    assert((Trimmed.allocatedSize() % PageSize) == 0);
    assert(M.base() <= Trimmed.base() &&
           Trimmed.allocatedSize() <= M.allocatedSize());

    return Trimmed;
}

std::error_code
LlvmliteMemoryManager::applyMemoryGroupPermissions(MemoryGroup &MemGroup,
                                                   unsigned Permissions) {
    for (sys::MemoryBlock &MB : MemGroup.PendingMem)
        if (std::error_code EC = MMapper.protectMappedMemory(MB, Permissions))
            return EC;

    MemGroup.PendingMem.clear();

    // Now go through free blocks and trim any of them that don't span the
    // entire page because one of the pending blocks may have overlapped it.
    for (FreeMemBlock &FreeMB : MemGroup.FreeMem) {
        FreeMB.Free = trimBlockToPageSize(FreeMB.Free);
        // We cleared the PendingMem list, so all these pointers are now invalid
        FreeMB.PendingPrefixIndex = (unsigned)-1;
    }

    // Remove all blocks which are now empty
    erase_if(MemGroup.FreeMem, [](FreeMemBlock &FreeMB) {
        return FreeMB.Free.allocatedSize() == 0;
    });

    return std::error_code();
}

void LlvmliteMemoryManager::invalidateInstructionCache() {
    for (sys::MemoryBlock &Block : CodeMem.PendingMem)
        sys::Memory::InvalidateInstructionCache(Block.base(),
                                                Block.allocatedSize());
}

LlvmliteMemoryManager::~LlvmliteMemoryManager() {
    for (MemoryGroup *Group : {&CodeMem, &RWDataMem, &RODataMem}) {
        for (sys::MemoryBlock &Block : Group->AllocatedMem)
            MMapper.releaseMappedMemory(Block);
    }
}

LlvmliteMemoryManager::MemoryMapper::~MemoryMapper() {}

void LlvmliteMemoryManager::anchor() {}

namespace {
// Trivial implementation of LlvmliteMemoryManager::MemoryMapper that just calls
// into sys::Memory.
class DefaultMMapper final : public LlvmliteMemoryManager::MemoryMapper {
  public:
    sys::MemoryBlock
    allocateMappedMemory(LlvmliteMemoryManager::AllocationPurpose Purpose,
                         size_t NumBytes,
                         const sys::MemoryBlock *const NearBlock,
                         unsigned Flags, std::error_code &EC) override {
        return sys::Memory::allocateMappedMemory(NumBytes, NearBlock, Flags,
                                                 EC);
    }

    std::error_code protectMappedMemory(const sys::MemoryBlock &Block,
                                        unsigned Flags) override {
        return sys::Memory::protectMappedMemory(Block, Flags);
    }

    std::error_code releaseMappedMemory(sys::MemoryBlock &M) override {
        return sys::Memory::releaseMappedMemory(M);
    }
};

DefaultMMapper DefaultMMapperInstance;
} // namespace

LlvmliteMemoryManager::LlvmliteMemoryManager(MemoryMapper *MM)
    : MMapper(MM ? *MM : DefaultMMapperInstance) {}

} // namespace llvm
