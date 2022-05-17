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
### Install package and configs
```
pip3 install . 
mkdir -p ~/.nexus/config/plugins.d
mkidr -p ~/.nexus/plugins/nexus
```

Change the docker volume bind location in the nexus.yml
```
cp config/nexus.yml ~/.nexus/config
cp config/plugins/* ~/.nexus/config/plugins.d
cp nexus/plugins/nexus/* ~/.nexus/plugins/nexus
```

## Setup Benchmark
To add a benchmark to Nexus, a schema file is necessary. 
The file name must have the **name** of the benchmark and should be written in **YAML**. 
For instance, the following [schema file](https://github.com/epicosy/nexus/blob/main/config/plugins/cgc.yml) defines the
CGC benchmark. The file should have the following structures/attributes:
- `name` - name of the benchmark;
  - `type` - benchmark;
  - `image`
    - `tag` - docker image tag;
    - `repo` - GitHub/DockerHub repository;
  - `container`
    - `name` - of the Docker container
    - `api`: 
      - `port` - Orbis API port number

After having the benchmark defined, you should create the benchmark instance by running:
```shell
$ nexus benchmark create -N __name_of_the_benchmark__
```

Then, you should install Orbis API for the benchmark instance you just created, by running:
```shell
$ nexus benchmark setup -N __name_of_the_benchmark__
```

At last, you should serve the Orbis API for the benchmark instance, by running:
```shell
$ nexus benchmark serve -N __name_of_the_benchmark__
```