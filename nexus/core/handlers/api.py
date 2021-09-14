import json
import requests

from requests import Response
from functools import wraps
from cement import Handler

from nexus.core.exc import NexusError
from nexus.core.interfaces.handlers import HandlersInterface


def debug_method(method):
    @wraps(method)
    def _impl(self, *method_args, **method_kwargs):
        debug_str = f"URL: {method_kwargs['endpoint_url']};"

        if 'json' in method_kwargs and method_kwargs['json']:
            debug_str += f" JSON: {method_kwargs['json']}"

        self.app.log.debug(debug_str, self.Meta.label)
        return method(self, *method_args, **method_kwargs)
    return _impl


class APIHandler(HandlersInterface, Handler):
    class Meta:
        label = 'api'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.url_format = "http://{ip}:{port}"

    def setup_cmds(self):
        return self.app.get_config('apis')[self.Meta.label]['setup']

    @debug_method
    def post(self, endpoint_url: str, json: dict = None) -> Response:
        return self.check_response(requests.post(url=endpoint_url, json=json))

    @debug_method
    def get(self, endpoint_url: str, json: dict = None) -> Response:
        return self.check_response(requests.get(url=endpoint_url, json=json))

    @staticmethod
    def check_response(response: Response):
        try:
            response_json = response.json()

            if not response_json:
                raise NexusError(f'API request to {response.url} returned empty response.')

            response_error = response_json.get('error', None)

            if response_error:
                raise NexusError(f"API request to {response.url} failed. {response_error}")

        except json.decoder.JSONDecodeError:
            pass

        if response.status_code != 200:
            raise NexusError(f'API request to {response.url} failed. {response.reason}')

        return response
