@echo on

@rem Display root environment (for debugging)
call conda list

@rem Create and populate environment
call conda create -n %CONDA_ENV% -q -y python=%PYTHON% cmake
if %errorlevel% neq 0 exit /b %errorlevel%

call activate %CONDA_ENV%
if %errorlevel% neq 0 exit /b %errorlevel%

@rem Install llvmdev
if "%LLVM%"=="16" (
  set LLVMDEV_CHANNEL="conda-forge"
) else (
  set LLVMDEV_CHANNEL="numba"
)

call conda install -y -q -c %LLVMDEV_CHANNEL% llvmdev="%LLVM%" libxml2
if %errorlevel% neq 0 exit /b %errorlevel%
