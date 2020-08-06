# README: Building ManyLinux2010 Wheels


## Build llvmdev packages for manylinux2010

Run the script below to start docker off building `llvmdev` base from the current state of the source tree:

- 32-bit linux: `./buildscripts/manylinux2010/docker_run_x32.sh build_llvmdev.sh`
- 64-bit linux: `./buildscripts/manylinux2010/docker_run_x64.sh build_llvmdev.sh`

The conda packages will be stored into `<llvmlite_source_root>/docker_output`

Note: the `docker_output` location can be used as a local conda channel.

Finally, upload the conda package to the numba channel under the "manylinux2010" label:

`anaconda upload -u numba -l manylinux2010 <filepath>`


## Build llvmlite wheel for manylinux2010

Run the script below to start docker off building `llvmlite` base from the current state of the source tree:

- 32-bit linux: `./buildscripts/manylinux2010/docker_run_x32.sh build_llvmlite.sh <pyver>`
- 64-bit linux: `./buildscripts/manylinux2010/docker_run_x64.sh build_llvmlite.sh <pyver>`

The conda packages will be stored into `<llvmlite_source_root>/docker_output/dist_<arch>_<pyver>`

Available Python installations (`<pyver>`) are:

- cp36-cp36m
- cp37-cp37m
- cp38-cp38


Reference: https://github.com/pypa/manylinux
