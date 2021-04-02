git clone https://github.com/zheng-broad/MERlin.git
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
echo ". $HOME/miniconda/etc/profile.d/conda.sh" >> ~/.bashrc
echo "conda activate" >> ~/.bashrc
source .bashrc
conda activate base
conda config --set always_yes true
conda config --set quiet true
conda create -n merlin_env python=3.6
source activate merlin_env
conda install rtree
conda install pytables
cd ~/MERlin
git checkout organization_updates
cd ~
pip install -e MERlin
pip install snakemake==5.12.0
pip install tifffile==0.14.0
pip install scikit-image==0.15.0

mkdir snake_outputs
mkdir slurm_outputs

