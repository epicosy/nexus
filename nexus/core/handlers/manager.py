from typing import List, Union

from cement import Handler
from docker.errors import NotFound, APIError
from docker.models.images import Image

from nexus.core.data.context import Context, Wrapper
from nexus.core.database import Instance
from nexus.core.exc import NexusError
from nexus.core.handlers.api import APIHandler
from nexus.core.handlers.nexus import NexusHandler
from nexus.core.interfaces.manager import ManagersInterface
from nexus.core.utils.misc import get_repo


class ContainerManager(ManagersInterface, Handler):
    class Meta:
        label = 'container'

    def all(self) -> List[Instance]:
        return self.app.db.query(Instance)

    def get_data(self, cid: int):
        return self.app.db.query(Instance, cid)

    def find(self, kind: str, name: str = None) -> Instance:
        return self.app.db.filter(Instance, {Instance.kind: lambda c_kind: c_kind == kind,
                                             Instance.name: lambda c_name: c_name == name}).first()

    def find_all(self, kind: str) -> List[Instance]:
        return self.app.db.filter(Instance, {Instance.kind: lambda c_kind: c_kind == kind})

    def register(self, image: str, container_id: str, volume: str, kind: str, name: str, ip: str, port: int) -> int:
        return self.app.db.add(Instance(image=image, id=container_id, name=name, volume=volume, kind=kind, ip=ip,
                                        status="created", port=port))

    def update(self, container_data: Instance, attr: str, value):
        self.app.db.update(entity=Instance, entity_id=container_data.id, attr=attr, value=value)

    def remove(self, instance: Instance):
        container = self.get(instance.id)

        if container and container.status == "running":
            self.app.log.warning(f"Stopping running container {container.name}")
            container.stop()
        
        if instance.volume:
            if container:
                container.remove(v=instance.volume)

        if container:
            self.app.log.warning(f"Removed container with id {container.id}.")

    def delete(self, kind: str, remove: bool = False, name: str = None) -> List[Instance]:
        instances = [self.find(kind, name)] if name else self.find_all(kind)

        for instance in instances:
            self.app.log.warning(f"Deleting record for {instance.name} {instance.name}")
            self.app.db.delete(Instance, instance.id)

            if remove:
                try:
                    self.app.log.warning(f"Removing container {instance.id[:10]} for {instance.name}")
                    self.remove(instance)
                except APIError as ae:
                    self.app.log.error(str(ae))

        return instances

    def get(self, name: str):
        try:
            return self.app.docker.containers.get(name)
        except NotFound as nf:
            self.app.log.error(str(nf))

            return None

    def get_ip(self, container_id: str):
        container = self.get(container_id)

        return container.attrs['NetworkSettings']['IPAddress']

    def volume(self):
        return self.app.docker.volumes.get(self.app.get_config('docker')['volume'])

    def setup(self, name: str, kind: str, api_handler: APIHandler, force: bool = False, env: dict = None):
        container_data = self.find(kind, name)

        if not container_data:
            self.app.log.error(f"{kind} {name} not found. "
                               f"To instantiate the {kind} use: nexus {kind} create -N {name}")
            exit(1)

        self.app.log.info(f"{container_data}")

        if container_data.status == 'setup' and not force:
            self.app.log.info(f"container {container_data.id[:10]} already setup for {kind} {container_data.name}.")
        else:
            container = self.get(container_data.id)

            if container.status != 'running':
                self.app.log.info(f"Running up {container_data.name} {kind} container.")
                container.start()
            self.app.log.info(f"Setting up container {container.id[:10]} for {kind} {container_data.name}")

            container_handler = self.app.handler.get('handlers', 'container', setup=True)
            configs = self.app.get_section(name)
            is_setup = container_handler.is_setup(container, container_data.kind)

            if not is_setup:
                is_setup = container_handler.setup(container, env=env,
                                                   cmds=api_handler.setup_cmds() + configs['container']['setup'])

            if is_setup:
                container_data = self.find(kind, name)
                self.update(container_data, attr='status', value='setup')
                self.update(container_data, attr='ip', value=self.get_ip(container_data.id))
                self.app.log.info(f"Updated records: {container_data}")

    def create(self, name: str, kind: str):
        configs = self.app.get_section(name)

        if not configs:
            self.app.log.error(f"Configurations for {kind} {name} not found")
            return

        if configs['type'] != kind:
            self.app.log.error(f"The {configs['type']} {name} is not of type {kind}.")
            return

        container_handler = self.app.handler.get('handlers', 'container', setup=True)

        # find container
        try:
            self.app.log.info(f"Looking for container {name}")
            container = self.get(name)

            if container:
                self.app.log.info(f"Found container {container.id[0:10]} {container.name}")
                container_data = self.find(kind, name)

                if not container_data:
                    container_data_id = self.register(image=configs['image']['tag'], container_id=container.id,
                                                      name=name, kind=kind, ip="",
                                                      port=configs['container']['api']['port'],
                                                      volume=self.app.get_config('docker')['volume'])
                    self.app.log.info(f"Registered container {container_data_id} for {kind} {self.app.pargs.name}.")
                else:
                    self.app.log.info(f"Container registered as {container_data}")

                return
        except APIError as e:
            self.app.log.error(str(e))
            exit(1)

        # check if image existed locally
        image = self.get_image(configs['image']['tag'])

        if not image:
            # try to pull from Dockerhub
            image = self.pull_image(configs['image']['tag'])

        if not image:
            # build image from tool/benchmark Github repository
            repo = get_repo(path=self.app.get_config('docker')['volume_bind'], repo_path=configs['image']['repo'],
                            logger=self.app.log)
            container_handler.build(path=repo.working_dir, tag=configs['image']['tag'])

        try:
            container_id = container_handler.create(image=configs['image']['tag'], name=name, volume=self.volume(),
                                                    container_configs=configs['container'])
            container_data_id = self.register(image=configs['image']['tag'], container_id=container_id, name=name,
                                              kind=kind, ip="", port=configs['container']['api']['port'],
                                              volume=self.app.get_config('docker')['volume'])
            self.app.log.info(f"Registered container {container_data_id} for {kind} {self.app.pargs.name}.")
        except (NexusError, APIError) as e:
            self.app.log.error(str(e))
            exit(1)

    def get_image(self, tag: str) -> Union[Image, None]:
        try:
            return self.app.docker.images.get(tag)
        except NotFound as nf:
            self.app.log.error(str(nf))

            return None

    def pull_image(self, tag: str) -> Union[Image, None]:
        try:
            self.app.log.info(f"Downloading {tag} from Dockerhub...")
            image = self.app.docker.images.pull(tag)
            self.app.log.info(f"Downloaded {tag}")
            return image
        except NotFound as nf:
            self.app.log.info(f"Not found {tag} on Dockerhub!")
            self.app.log.error(str(nf))

            return None

    def refresh(self, name: str, kind: str):
        container_data = self.find(kind, name)
        ip = self.get_ip(container_id=container_data.id)

        if ip != container_data.ip:
            self.app.log.info(f"Updating {container_data.name}'s ip from {container_data.ip} to {ip}")
            self.update(container_data, 'ip', ip)

    def start(self, container_id: str):
        container = self.get(container_id)

        # Start containers if these are not running

        if container and container.status != 'running':
            self.app.log.info(f"Starting {container.name} benchmark container.")
            container.start()

    def serve(self, name: str, kind: str, api_handler: APIHandler):
        container_data = self.find(kind, name)

        if not container_data:
            self.app.log.warning(f"{kind} {name} does not exist")
            return

        if api_handler.is_running(container_data):
            self.app.log.warning(f"{kind} {name} server is running")
            return

        container = self.get(container_data.id)

        if container.status != 'running':
            self.app.log.info(f"Running up {container_data.name} {kind} container.")
            container.start()

        container_handler = self.app.handler.get('handlers', 'container', setup=True)
        container_handler.setup(container, cmds=api_handler.serve_cmd())


class NexusManager(ManagersInterface, Handler):
    class Meta:
        label = 'nexus'

    def get_wrapper(self, name: str, kind: str) -> Wrapper:
        container_manager = self.app.handler.get('managers', 'container', setup=True)
        instance = container_manager.find(kind, name)

        if not instance:
            raise NexusError(f"{kind} {name} not created.")

        if instance.status != 'setup':
            raise NexusError(f"{kind} {name} not setup.")

        container = container_manager.get(instance.id)

        if not container:
            raise NexusError(f"{kind} {name}'s container ({instance.id}) not found.")

        container_manager.start(instance.id)

        return Wrapper(instance=instance, container=container)

    def get_context(self, nexus_handler: NexusHandler) -> Context:
        benchmark = self.get_wrapper(nexus_handler.benchmark, 'benchmark')
        tool = self.get_wrapper(nexus_handler.tool, 'tool')

        return Context(tool=tool, benchmark=benchmark)
