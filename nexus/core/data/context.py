from dataclasses import dataclass

from docker.models.containers import Container

from nexus.core.database import Instance


@dataclass
class Wrapper:
    instance: Instance
    container: Container


@dataclass
class Context:
    tool: Wrapper
    benchmark: Wrapper
