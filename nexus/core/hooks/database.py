from sqlalchemy.exc import OperationalError

from nexus.core.database import Database
from nexus.core.exc import NexusError


def init_database(app):
    try:
        database = Database(dialect=app.get_config('dialect'), username=app.get_config('username'),
                            password=app.get_config('password'), host=app.get_config('host'),
                            port=app.get_config('port'), database=app.get_config('database'),
                            debug=app.config.get('log.colorlog', 'database'))

        app.extend('db', database)

    except OperationalError as oe:
        raise NexusError(oe)


def load(app):
    app.hook.register('post_setup', init_database)
