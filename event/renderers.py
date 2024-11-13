from rest_framework.renderers import BaseRenderer
import orjson

class ORJSONRenderer(BaseRenderer):
    media_type = 'application/json'
    format = 'json'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''
        return orjson.dumps(data)