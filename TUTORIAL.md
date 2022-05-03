## Install Nexus
### download repo
git clone https://github.com/epicosy/nexus
cd nexus
### Install dependencies
./install_deps.sh
pip3 install -r requirements.txt

### Init database
./init_db.sh 

### install package and configs
pip3 install . 
mkdir -p ~/.nexus/config/plugins.d
mkidr -p ~/.nexus/plugins/nexus

Change the docker volume bind locaition in the nexus.yml
cp config/nexus.yml ~/.nexus/config
cp nexus/plugins/nexus/* ~/.nexus/plugins/nexus

