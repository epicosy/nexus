from dataclasses import dataclass

from nexus.core.database import Instance
from nexus.core.handlers.orbis import OrbisHandler
from nexus.core.handlers.synapser import SynapserHandler


@dataclass
class Context:
    synapser: SynapserHandler
    tool: Instance
    orbis: OrbisHandler
    benchmark: Instance
    working_dir: str
