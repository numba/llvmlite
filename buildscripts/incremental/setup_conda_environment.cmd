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
conda create -n %CONDA_ENV% -q -y python=%PYTHON% cmake

call activate %CONDA_ENV%
@rem Install llvmdev
%CONDA_INSTALL% -c numba llvmdev="3.9*"
@rem Install enum34 for Python < 3.4
if %PYTHON% LSS 3.4 (%CONDA_INSTALL% enum34)
