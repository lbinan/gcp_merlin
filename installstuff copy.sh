git clone https://github.com/zheng-broad/MERlin.git
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
echo ". $HOME/miniconda/etc/profile.d/conda.sh" >> ~/.bashrc
echo "conda activate" >> ~/.bashrc
source .bashrc
conda activate base
conda config --set always_yes true
conda config --set quiet true
conda env create -f environment.yml
conda activate merlin_env
cd ~/MERlin
git checkout organization_updates
cd ~
pip install -e MERlin
