from abc import ABC
from pathlib import Path

from docker.models.containers import Container

from nexus.core.data.store import Program
from nexus.core.handlers.docker import DockerHandler
from nexus.core.data.results import CommandData
from nexus.core.interfaces.nexus import NexusInterface


class NexusHandler(NexusInterface, DockerHandler, ABC):
    class Meta:
        label = 'nexus'


class LocalNexus(NexusHandler, ABC):
    class Meta:
        label = 'local_nexus'

    def __call__(self, container: Container, cmd_str, args: str = "", call: bool = True, **kwargs) -> CommandData:
        cmd_data = CommandData(f"{cmd_str} {args}" if args else cmd_str)

        if call:
            return self.command(container=container, cmd_data=cmd_data, **kwargs)

        return cmd_data


class RemoteNexus(NexusHandler, ABC):
    class Meta:
        label = 'remote_nexus'

    def __call__(self, *args, **kwargs):
        return super(RemoteNexus, self).__call__(*args, **kwargs)
