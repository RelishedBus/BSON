# type: ignore
import typing as tp
import struct
import inspect
from dataclasses import is_dataclass
from datetime import datetime
from collections import OrderedDict


from .bson_error import ( # noqa: F401
BsonUnsupportedKeyError,
BsonCycleDetectedError, BsonStringTooBigError,
BsonDocumentTooBigError, BsonBinaryTooBigError, BsonIntegerTooBigError, BsonUnsupportedObjectError,
BsonKeyWithZeroByteError,
)

def _helper_cycle_check_dict(data: dict[tp.Any, tp.Any]) -> None:
    try:
        for key in data:
            if isinstance(data[key], dict):
                _helper_cycle_check_dict(data[key])
    except RecursionError:
        raise BsonCycleDetectedError('Обнаружен цикл!!!')

def _check_property(obj: tp.Any) -> bool:
    try:
        for attr_name, attr_value in vars(obj.__class__).items():
            if isinstance(attr_value, property):
                return True
    except Exception:
        raise BsonCycleDetectedError('В проперти есть циклы')
    return False

def _cast_tuple_to_dict(data: tp.NamedTuple)->dict[str, tp.Any]:
    tmp_dict: dict[str, tp.Any] = data._asdict()
    result: OrderedDict[tp.Any, tp.Any] = OrderedDict()
    for f in data._fields:
        result[f] = tmp_dict[f]
    return result

def _cast_dataclass_to_dict(data: tp.Any) -> dict[str, tp.Any]:
    if not hasattr(data, '__annotations__'):
        return {}
    tmp_dict: dict[str, tp.Any] = data.__annotations__
    result: OrderedDict[tp.Any, tp.Any] = OrderedDict()
    for f in tmp_dict:
        result[f] = getattr(data, f)
    return result

def _cast_property_to_dict(data: tp.Any) -> dict[str, tp.Any]:
    result: OrderedDict[tp.Any, tp.Any] = OrderedDict()
    for name, value in inspect.getmembers(data.__class__):
        try:
            if isinstance(value, property):
                result[name] = getattr(data, name)
        except RecursionError:
            raise RecursionError('В проперти есть циклы')
        except Exception:
            continue
    if not result:
        raise BsonUnsupportedObjectError('Объект не поддерживается, не имеет читаемых проперти')
    return result

def marshal(data: dict[str, tp.Any] | tp.OrderedDict[str, tp.Any], keep_types: bool = False)\
        -> bytes:
    if isinstance(data, tuple) and hasattr(data, '_fields'):
        data = _cast_tuple_to_dict(data)
    elif is_dataclass(data):
        data = _cast_dataclass_to_dict(data)
    elif _check_property(data):
        data = _cast_property_to_dict(data)
    elif not isinstance(data, dict):
        raise BsonUnsupportedObjectError("Позвольте, сударь, как это парсить?")

    res: list[int] = [0, 0, 0, 0]
    if not data:
        return bytes([5, 0, 0, 0, 0])
    else:
        ###pre-check
        for key in data:
            if not isinstance(key, str):
                raise BsonUnsupportedKeyError('pls give me norm key')
        for key in data:
            if isinstance(key, str) and chr(0) in key:
                raise BsonKeyWithZeroByteError('without zero(chr(0)) pls!')
        for key in data:
            if (not isinstance(data[key], (type(None), bool, str, float, int, datetime, bytes,
                                          bytearray, list, tuple, dict, OrderedDict)) and not is_dataclass(data[key])
                    and not _check_property(data[key])):
                raise BsonUnsupportedObjectError('unsupported object')
        for key in data if isinstance(data, OrderedDict) else sorted(data.keys()):
            IND_OF_TYPE: int = 0

            #####################
            ##translate the key##
            #####################
            tmp_byte_array_name: list[int] = []
            ### if e_name is string

            if isinstance(key, str):
                tmp_byte_array_name.append(0)
                IND_OF_TYPE = len(res)
                try:
                    tmp_byte_array_name.extend(list(key.encode('utf-8')))
                except UnicodeEncodeError:
                    raise BsonStringTooBigError('too long str')
                tmp_byte_array_name.append(0) #unsigned_byte(0)

            res.extend(tmp_byte_array_name)

            #######################
            ## translate the data##
            #######################

            tmp_byte_array_data: list[int] = []

            ###if data is string
            if isinstance(data[key], str):
                res[IND_OF_TYPE] = 2
                try:
                    tmp_byte_array_data.extend(struct.pack('<i', len(data[key]) + 1))
                    tmp_byte_array_data.extend(data[key].encode('utf-8'))
                except UnicodeEncodeError:
                    raise BsonStringTooBigError('too long str')
                tmp_byte_array_data.append(0)
            ###if data is boolean
            elif isinstance(data[key], bool):
                res[IND_OF_TYPE] = 8
                if data[key]:
                    tmp_byte_array_data.append(1)
                else:
                    tmp_byte_array_data.append(0)
            ###if data is float
            elif isinstance(data[key], float):
                res[IND_OF_TYPE] = 1
                if data[key] == float('inf'):
                    tmp_byte_array_data.extend(struct.pack('<d', data[key]))
                else:
                    tmp_byte_array_data.extend(struct.pack('d', data[key]))

            ###if data is int
            elif isinstance(data[key], int):
                if -2 ** 31 <= data[key] <= 2 ** 31 - 1:
                    res[IND_OF_TYPE] = 16
                    tmp_byte_array_data.extend(struct.pack('<i', data[key]))
                elif -2 ** 63 <= data[key] <= 2 ** 63 - 1:
                    res[IND_OF_TYPE] = 18
                    tmp_byte_array_data.extend(struct.pack('<q', data[key]))
                else:
                    raise BsonIntegerTooBigError('too big integer')

            ###if data is None
            elif data[key] is None:
                res[IND_OF_TYPE] = 10

            ###if data is datetime
            elif isinstance(data[key], datetime):
                res[IND_OF_TYPE] = 9
                tmp_byte_array_data.extend(struct.pack('<q', int(data[key].timestamp() * 1000)))
                #tmp_byte_array_data.reverse()

            ###if data is bytes or bytearray
            elif isinstance(data[key], bytes) or isinstance(data[key],bytearray):
                if len(data[key]) > 2 ** 31 - 1:
                    raise BsonBinaryTooBigError("много байтов")
                res[IND_OF_TYPE] = 5

                tmp_byte_array_data.extend(struct.pack('<i', len(data[key])))

                tmp_byte_array_data.append(0)
                tmp_byte_array_data.extend(data[key])

            ###if data is dict
            elif (((isinstance(data[key], dict) or
                  (isinstance(data[key], tuple) and hasattr(data[key], '_fields'))) or
                  is_dataclass(data[key])) or
                  _check_property(data[key])):
                ###hard check
                if isinstance(data[key], tuple) and hasattr(data[key], '_fields'):
                    data[key] = _cast_tuple_to_dict(data[key])
                elif is_dataclass(data[key]):
                    data[key] = _cast_dataclass_to_dict(data[key])
                elif _check_property(data[key]):
                    try:
                        data[key] = _cast_property_to_dict(data[key])
                    except RecursionError:
                        raise BsonCycleDetectedError('В проперти есть циклы')
                _helper_cycle_check_dict(data[key])

                res[IND_OF_TYPE] = 3
                tmp_byte_array_data.extend(marshal(data[key], keep_types))
            ###if data is array(list)
            elif isinstance(data[key], list) or isinstance(data[key], tuple):
                try:
                    res[IND_OF_TYPE] = 4
                    dict_helper: tp.OrderedDict[str, tp.Any] =\
                        OrderedDict([(str(ind), value) for ind, value in enumerate(data[key])])
                    tmp_byte_array_data.extend(marshal(dict_helper, keep_types))
                except RecursionError:
                    raise BsonCycleDetectedError('Обнаружен цикл!')

            res.extend(tmp_byte_array_data)

            if len(res) > 2**31-1:
                raise BsonDocumentTooBigError("too large document")
        ###ADD METADATA
        if keep_types:
            metadata_str: list[str] | str = [type(data[x]).__name__ if
                                             isinstance(data[x], (tuple, bytearray)) else "" for x in
                                             (data if isinstance(data, OrderedDict) else sorted(list(data.keys())))]
            if metadata_str and ('tuple' in metadata_str or 'bytearray' in metadata_str):
                metadata_str = ':'.join(metadata_str)
                meta_key: bytes = '__metadata__'.encode('utf-8')
                res.append(5)
                res.extend(meta_key)
                res.append(0)
                encoded_meta: bytes = metadata_str.encode('utf-8')
                res.extend(struct.pack('<i', len(encoded_meta)))
                res.append(128)
                res.extend(encoded_meta)


        res.append(0) # unsigned_byte(0)
        res[0:4] = struct.pack('<i', len(res)) #update size
        return bytes(res)
