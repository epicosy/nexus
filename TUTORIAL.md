## Install Nexus
### Download repo
```shell
git clone https://github.com/epicosy/nexus
cd nexus
```
### Install dependencies
```shell
./install_deps.sh
pip3 install -r requirements.txt
```

### Init database
```shell
./init_db.sh 
```
If it fails, use ```sudo -i -u postgres```
### install package and configs
```
pip3 install . 
mkdir -p ~/.nexus/config/plugins.d
mkidr -p ~/.nexus/plugins/nexus
```

Change the docker volume bind locaition in the nexus.yml
```
cp config/nexus.yml ~/.nexus/config
cp nexus/plugins/nexus/* ~/.nexus/plugins/nexus
```
