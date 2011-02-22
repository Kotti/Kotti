import json

from sqlalchemy.types import TypeDecorator, VARCHAR

class JsonType(TypeDecorator):
    """http://www.sqlalchemy.org/docs/core/types.html#marshal-json-strings
    """
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
