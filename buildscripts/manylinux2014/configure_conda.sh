# Setup miniconda environment that is compatible with manylinux2014 docker image
conda install -y conda conda-build anaconda-client
# # Pin conda and conda-build versions that are known to be compatible
# echo "conda ==4.3.25" >> /root/miniconda3/conda-meta/pinned
# echo "conda-build ==3.0.9" >> /root/miniconda3/conda-meta/pinned
