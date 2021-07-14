
import docker
from nexus.core.exc import NexusError


def bind_docker(app):
    try:
        docker_client = docker.from_env(timeout=10)
        assert docker_client.ping()
        app.extend('docker', docker_client)
    except AssertionError:
        raise NexusError("Could not connect to the Docker Client")


def load(app):
    app.hook.register('post_setup', bind_docker)
