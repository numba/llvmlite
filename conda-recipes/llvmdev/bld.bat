setlocal EnableDelayedExpansion
FOR /D %%d IN (llvm-*.src) DO (MKLINK /J llvm %%d
if !errorlevel! neq 0 exit /b %errorlevel%)
FOR /D %%d IN (lld-*.src) DO (MKLINK /J lld %%d
if !errorlevel! neq 0 exit /b %errorlevel%)
FOR /D %%d IN (unwind\libunwind-*.src) DO (MKLINK /J libunwind %%d
if !errorlevel! neq 0 exit /b %errorlevel%)

DIR

mkdir build
cd build

set BUILD_CONFIG=Release

REM === Configure step ===

REM allow setting the targets to build as an environment variable
REM default is LLVM 11 default architectures + RISCV.  Can remove this entire option in LLVM 13
if "%LLVM_TARGETS_TO_BUILD%"=="" (
    set "LLVM_TARGETS_TO_BUILD=host;AArch64;AMDGPU;ARM;BPF;Hexagon;Mips;MSP430;NVPTX;PowerPC;Sparc;SystemZ;X86;XCore;RISCV"
)
if "%ARCH%"=="32" (
    set "ARCH_POSTFIX="
    set "GEN_ARCH=Win32"
) else (
    set "ARCH_POSTFIX= Win64"
    set "GEN_ARCH=x64"
)

REM The platform toolset host arch is set to x64 so as to use the 64bit linker,
REM the 32bit linker heap is too small for llvm8 so it tries and falls over to
REM the 64bit linker anyway. This must be passed in to certain generators as
REM '-Thost x64'.
set PreferredToolArchitecture=x64

set MAX_INDEX_CMAKE_GENERATOR=0

set "CMAKE_GENERATOR[0]=Visual Studio 16 2019"

set "CMAKE_GENERATOR_ARCHITECTURE[0]=%GEN_ARCH%"

set "CMAKE_GENERATOR_TOOLSET[0]=v142"

REM Reduce build times and package size by removing unused stuff
REM BENCHMARKS (new for llvm8) don't build under Visual Studio 14 2015
set CMAKE_CUSTOM=-DLLVM_TARGETS_TO_BUILD="%LLVM_TARGETS_TO_BUILD%" ^
    -DLLVM_ENABLE_PROJECTS:STRING=lld ^
    -DLLVM_INCLUDE_UTILS=ON ^
    -DLLVM_INCLUDE_DOCS=OFF ^
    -DLLVM_INCLUDE_EXAMPLES=OFF ^
    -DLLVM_ENABLE_ASSERTIONS=ON ^
    -DLLVM_USE_INTEL_JITEVENTS=ON ^
    -DLLVM_INCLUDE_BENCHMARKS=OFF ^
    -DLLVM_ENABLE_DIA_SDK=OFF ^
    -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly

REM try all compatible visual studio toolsets to find one that is installed
setlocal enabledelayedexpansion
for /l %%n in (0,1,%MAX_INDEX_CMAKE_GENERATOR%) do (
    cmake -G "!CMAKE_GENERATOR[%%n]!" ^
          -A "!CMAKE_GENERATOR_ARCHITECTURE[%%n]!" ^
          -T "!CMAKE_GENERATOR_TOOLSET[%%n]!" ^
          -DCMAKE_BUILD_TYPE="%BUILD_CONFIG%" ^
          -DCMAKE_PREFIX_PATH="%LIBRARY_PREFIX%" ^
          -DCMAKE_INSTALL_PREFIX:PATH="%LIBRARY_PREFIX%" ^
          %CMAKE_CUSTOM% "%SRC_DIR%\llvm"
    if not errorlevel 1 goto configuration_successful
    del CMakeCache.txt
)

REM no compatible visual studio toolset was found
if errorlevel 1 exit 1

:configuration_successful
endlocal

REM === Build step ===
cmake --build . --config "%BUILD_CONFIG%"
if errorlevel 1 exit 1

REM === Install step ===
cmake --build . --config "%BUILD_CONFIG%" --target install
if errorlevel 1 exit 1

REM From: https://github.com/conda-forge/llvmdev-feedstock/pull/53
"%BUILD_CONFIG%\bin\opt" -S -vector-library=SVML -mcpu=haswell -O3 "%RECIPE_DIR%\numba-3016.ll" | "%BUILD_CONFIG%\bin\FileCheck" "%RECIPE_DIR%\numba-3016.ll"
if errorlevel 1 exit 1

REM This is technically how to run the suite, but it will only run in an
REM enhanced unix-like shell which has functions like `grep` available.
REM cd ..\test
REM "%PYTHON%" "..\build\%BUILD_CONFIG%\bin\llvm-lit.py" -vv Transforms ExecutionEngine Analysis CodeGen/X86
REM if errorlevel 1 exit 1
