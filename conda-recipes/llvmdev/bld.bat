mkdir build
cd build

set BUILD_CONFIG=Release

REM === Configure step ===

REM allow setting the targets to build as an environment variable
if "%LLVM_TARGETS_TO_BUILD%"=="" (
    set "LLVM_TARGETS_TO_BUILD=host;AMDGPU;NVPTX"
)
set CMAKE_GENERATOR="Visual Studio 16 2019"
set CMAKE_GENERATOR_TOOLSET="v141"


REM Reduce build times and package size by removing unused stuff
set CMAKE_CUSTOM=-DLLVM_TARGETS_TO_BUILD="%LLVM_TARGETS_TO_BUILD%" ^
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_UTILS=ON -DLLVM_INCLUDE_DOCS=OFF ^
    -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_ENABLE_ASSERTIONS=ON ^
    -DLLVM_USE_INTEL_JITEVENTS=ON ^
    -DLLVM_INCLUDE_BENCHMARKS=OFF ^
    -DLLVM_ENABLE_DIA_SDK=OFF ^
    -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=WebAssembly

cmake -G "%CMAKE_GENERATOR%" -T "%CMAKE_GENERATOR_TOOLSET%" ^
    -DCMAKE_BUILD_TYPE="%BUILD_CONFIG%" -DCMAKE_PREFIX_PATH="%LIBRARY_PREFIX%" ^
    -DCMAKE_INSTALL_PREFIX:PATH="%LIBRARY_PREFIX%" %CMAKE_CUSTOM% "%SRC_DIR%"


REM === Build step ===
cmake --build . --config "%BUILD_CONFIG%"

REM === Install step ===
cmake --build . --config "%BUILD_CONFIG%" --target install

REM From: https://github.com/conda-forge/llvmdev-feedstock/pull/53
"%BUILD_CONFIG%\bin\opt" -S -vector-library=SVML -mcpu=haswell -O3 "%RECIPE_DIR%\numba-3016.ll" | "%BUILD_CONFIG%\bin\FileCheck" "%RECIPE_DIR%\numba-3016.ll"

REM This is technically how to run the suite, but it will only run in an
REM enhanced unix-like shell which has functions like `grep` available.
REM cd ..\test
REM "%PYTHON%" "..\build\%BUILD_CONFIG%\bin\llvm-lit.py" -vv Transforms ExecutionEngine Analysis CodeGen/X86
REM if errorlevel 1 exit 1
