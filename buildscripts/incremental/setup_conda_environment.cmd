@rem The cmd /C hack circumvents a regression where conda installs a conda.bat
@rem script in non-root environments.
set CONDA_INSTALL=cmd /C conda install -q -y
set PIP_INSTALL=pip install -q

@echo on

@rem Deactivate any environment
call deactivate
@rem Display root environment (for debugging)
conda list
@rem Clean up any left-over from a previous build
conda remove --all -q -y -n %CONDA_ENV%

@rem Create and populate environment
conda create -n %CONDA_ENV% -q -y python=%PYTHON%

call activate %CONDA_ENV%
@rem Install llvmdev (separate channel, for now)
%CONDA_INSTALL% -c numba -n %CONDA_ENV% llvmdev="3.7*" llvmlite
@rem Install required backports for older Pythons
if %PYTHON% LSS 3.4 (%CONDA_INSTALL% enum34)
