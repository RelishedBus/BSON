# type: ignore
import typing as tp

from bson.bson_decode import unmarshal # noqa: F401
from bson.bson_encode import marshal # noqa: F401

from bson.bson_error import MapperUnsupportedOptionError # noqa: F401


class Mapper:
    def __init__(self, **kwargs: tp.Any) -> None:
        self.__metadata__: bytes = bytes()
        self._supported_options: dict[tp.Any, tp.Any] = {
        'python_only' : False,
        'keep_types' : False
        }
        for key, value in kwargs.items():
            if key not in self._supported_options:
                raise MapperUnsupportedOptionError('Опция не поддерживается')
            self._supported_options[key] = value

    @property
    def python_only(self) -> bool:
        return self._supported_options['python_only']

    @property
    def keep_types(self) -> bool:
        return self._supported_options['keep_types']

    def marshal(self, data: dict[str, tp.Any]) -> bytes:
        return marshal(data, self.keep_types)

    def unmarshal(self, data: bytes) -> dict[str, tp.Any]:
        return unmarshal(data, self.python_only, self.keep_types)


