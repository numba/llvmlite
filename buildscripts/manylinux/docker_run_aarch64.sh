export MANYLINUX_IMAGE="manylinux_2_28_aarch64"
export MINICONDA_FILE="https://repo.anaconda.com/miniconda/Miniconda3-py311_24.9.2-0-Linux-aarch64.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
