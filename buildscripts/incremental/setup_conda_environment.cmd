@echo on

@rem Display root environment (for debugging)
call conda list

@rem Clean up any left-over from a previous build
call conda remove --all -q -y -n %CONDA_ENV%

@rem Create and populate environment
call conda create -n %CONDA_ENV% -q -y python=%PYTHON% cmake
if %errorlevel% neq 0 exit /b %errorlevel%

call activate %CONDA_ENV%
if %errorlevel% neq 0 exit /b %errorlevel%

@rem Install llvmdev
if "%LLVM%"=="15" (
  set LLVMDEV_CHANNEL="conda-forge"
) else (
  set LLVMDEV_CHANNEL="numba/label/dev"
)

call conda install -y -q -c %LLVMDEV_CHANNEL% llvmdev="%LLVM%" libxml2
if %errorlevel% neq 0 exit /b %errorlevel%
