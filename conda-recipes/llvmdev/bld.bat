mkdir build
cd build

set BUILD_CONFIG=Release

REM Configure step
set CMAKE_GENERATOR=Visual Studio 15 2017
if "%ARCH%"=="32" (
    set CMAKE_GENERATOR_ARCH=Win32
) else (
    set CMAKE_GENERATOR_ARCH=x64
)
set CMAKE_GENERATOR_TOOLSET=v141

REM llvm 8 needs the 64bit linker
set PreferredToolArchitecture=x64

REM Reduce build times and package size by removing unused stuff
REM BENCHMARKS (new for llvm8) don't build under Visual Studio 14 2015
set CMAKE_CUSTOM=-DLLVM_TARGETS_TO_BUILD="host;AMDGPU;NVPTX" ^
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_UTILS=ON -DLLVM_INCLUDE_DOCS=OFF ^
    -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_ENABLE_ASSERTIONS=ON ^
    -DLLVM_USE_INTEL_JITEVENTS=ON ^
    -DLLVM_INCLUDE_BENCHMARKS=OFF ^
    -DLLVM_ENABLE_DIA_SDK=OFF ^
    -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly

REM the platform toolset host arch is set to x64 so as to use the 64bit linker,
REM the 32bit linker heap is too small for llvm8 so it tries and falls over to
REM the 64bit linker anyway
cmake -G "%CMAKE_GENERATOR%" -A "%CMAKE_GENERATOR_ARCH%" -T "%CMAKE_GENERATOR_TOOLSET%" ^
    -DCMAKE_BUILD_TYPE="%BUILD_CONFIG%" -DCMAKE_PREFIX_PATH=%LIBRARY_PREFIX% ^
    -DCMAKE_INSTALL_PREFIX:PATH=%LIBRARY_PREFIX% %CMAKE_CUSTOM% %SRC_DIR% ^
    -DCMAKE_VS_PLATFORM_TOOLSET_HOST_ARCHITECTURE=x64
if errorlevel 1 exit 1

REM Build step
cmake --build . --config "%BUILD_CONFIG%"
if errorlevel 1 exit 1

REM Install step
cmake --build . --config "%BUILD_CONFIG%" --target install
if errorlevel 1 exit 1

REM From: https://github.com/conda-forge/llvmdev-feedstock/pull/53
%BUILD_CONFIG%\bin\opt -S -vector-library=SVML -mcpu=haswell -O3 %RECIPE_DIR%\numba-3016.ll | %BUILD_CONFIG%\bin\FileCheck %RECIPE_DIR%\numba-3016.ll
if errorlevel 1 exit 1

REM This is technically how to run the suite, but it will only run in an
REM enhanced unix-like shell which has functions like `grep` available.
REM cd ..\test
REM %PYTHON% ..\build\%BUILD_CONFIG%\bin\llvm-lit.py -vv Transforms ExecutionEngine Analysis CodeGen/X86
REM if errorlevel 1 exit 1
