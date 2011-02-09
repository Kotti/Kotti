import json

from sqlalchemy import types

class JsonType(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, engine):
        return unicode(json.dumps(value))

    def process_result_value(self, value, engine):
        return json.loads(value)

    def copy(self):
        return JsonType(self.impl.length)
