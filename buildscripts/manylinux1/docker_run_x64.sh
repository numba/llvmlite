export ARCH="x86_64"
export MINICONDA_FILE="Miniconda3-3.19.0-Linux-x86_64.sh"
cd $(dirname $0)
./docker_run.sh $1 $2
