# README: Building manylinux Wheels


## Build llvmdev conda packages for use during manylinux wheel building

Run the script below to start docker off building `llvmdev` base from the current state of the source tree:

- x86_64 linux: `./buildscripts/manylinux/docker_run_x64.sh build_llvmdev.sh`
    - uses manylinux2014 image for glibc 2.17+: `pypa.io/pypa/manylinux2014_x86_64`
- aarch64 linux: `./buildscripts/manylinux/docker_run_aarch64.sh build_llvmdev.sh`
    - uses manylinux_2_28 image for glibc 2.28+: `pypa.io/pypa/manylinux_2_28_aarch64`

The conda packages will be stored into `<llvmlite_source_root>/docker_output`

Note: the `docker_output` location can be used as a local conda channel.

Finally, upload the conda package to the numba channel under the "manylinux_x_y" 
label (`x` and `y` are glibc major and minor version numbers, respectively):

`anaconda upload -u numba -l manylinux_x_y <filepath>`


## Build llvmlite wheel for manylinux

Run the script below to start docker off building `llvmlite` base from the current state of the source tree:

- x86_64 linux: `./buildscripts/manylinux/docker_run_x64.sh build_llvmlite.sh <pyver>`
- aarch64 linux: `./buildscripts/manylinux/docker_run_aarch64.sh build_llvmlite.sh <pyver>`

The conda packages will be stored into `<llvmlite_source_root>/docker_output/dist_<arch>_<pyver>`

Available Python installations (`<pyver>`) are:

- cp310-cp310
- cp311-cp311
- cp312-cp312
- cp313-cp313


Reference: https://github.com/pypa/manylinux
