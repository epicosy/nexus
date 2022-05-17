# Maestro Platform
Maestro is platform that provides an accessible
means of performing automated repair of software vulnerabilities isolated environments and in an out-of-the-box manner. 
Maestro has a decentralized and microservice-based architecture based on Docker containers. 
Maestro is composed of an orchestration component, Nexus, and two components Orbis and Synapser, that respectively 
convert tools and benchmarks into microservices. To integrate a tool or benchmark in Maestro, a developer only needs to 
develop a plugin for its respective component, Synapser or Orbis. For Nexus, the plugin connects with Synapser and 
Orbis, and it is necessary for each tool/benchmark pair.

![Maestro architecture](maestro_arch.png)

## Install Nexus
To install Nexus, perform the following steps:

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
Also, the benchmark should provide the necessary bindings for Orbis, 
for that please follow [this tutorial](https://github.com/epicosy/orbis/blob/main/TUTORIAL.md).
The file name must have the **name** of the benchmark and should be written in **YAML**. 
For instance, the following [schema file](https://github.com/epicosy/nexus/blob/main/config/plugins/cgc.yml) defines the
CGC benchmark. The file should have the following structures/attributes:
- `name` - name of the benchmark;
  - `type` - benchmark;
  - `image`
    - `tag` - docker image tag;
    - `repo` - GitHub/DockerHub repository (e.g. [CGC](https://github.com/epicosy/cgc));
  - `container`
    - `name` - of the Docker container
    - `api`: 
      - `port` - Orbis API port number

After having the benchmark defined, you should create the benchmark instance by running:
```shell
$ nexus benchmark create -N __name_of_the_benchmark__
```

Then, you should install the Orbis API for the benchmark instance by running:
```shell
$ nexus benchmark setup -N __name_of_the_benchmark__
```

At last, you should serve the Orbis API for the benchmark instance with:
```shell
$ nexus benchmark serve -N __name_of_the_benchmark__
```

## Setup Tool
Adding a tool to Nexus is similar to adding a benchmark. 
You should also create a schema file that follows the structure and attributes introduced above for the benchmark.
The only different attribute is the `type`, it must be set to **tool**. 
The following [schema file](https://github.com/epicosy/nexus/blob/main/config/plugins/genprog.yml) defines the
[GenProg tool](https://github.com/epicosy/genprog-code).
Providing, setting up, and serving the tool is similar to the steps above:
```shell
$ nexus tool create -N __name_of_the_tool__
$ nexus tool setup -N __name_of_the_tool__
$ nexus tool serve -N __name_of_the_tool__
```