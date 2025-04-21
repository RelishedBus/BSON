import typing as tp
import struct
from datetime import datetime, timezone

from .bson_error import ( # noqa: F401
BsonBrokenDataError, BsonStringSizeError,
BsonNotEnoughDataError, BsonBadKeyDataError, BsonBadStringDataError, BsonRepeatedKeyDataError,
BsonInvalidArrayError,
BsonIncorrectSizeError, BsonInconsistentStringSizeError, BsonTooManyDataError, BsonInvalidElementTypeError,
BsonInvalidBinarySubtypeError, BsonBadArrayIndexError,
)
metadata_inter: list[str] = []
def _decode_string(data: bytes, ind: int, size_of_document: int)-> tuple[str, int]:
    size_of_str_data, = struct.unpack('<i', bytes(data[ind:ind + 4]))
    if size_of_str_data <= 0:
        raise BsonStringSizeError("negative string???")
    if size_of_str_data > size_of_document or ind + 3 + size_of_str_data >= size_of_document - 1:
        raise BsonInconsistentStringSizeError("unreal str///")

    tmp_str = []
    ind_to_zero: int = ind + 4

    while data[ind_to_zero] != 0 or ind_to_zero < ind + 4 + size_of_str_data - 1:
        if data[ind_to_zero] == 00:
            tmp_str.append(00)
        else:
            tmp_str.append(data[ind_to_zero])
        ind_to_zero += 1
    ind += 4 + len(tmp_str) - 1
    if data[ind + 1] != 0 or data[ind + 1] == 0 and ind + 1 == len(data) - 1:
        raise BsonBrokenDataError('where is end zero?')

    try:
        decoded_str = bytes(tmp_str).decode('utf-8')
    except Exception:
        raise BsonBadStringDataError('check utf-8')

    return decoded_str, ind + 1

def _decode_cstring(data:bytes, ind: int) -> tuple[str, int]:
    try:
        end_of_key: int = data.index(0, ind)
        key_bytes: bytes = data[ind: end_of_key]
    except ValueError:
        raise BsonBrokenDataError('Отсутсвует ноль в конце cstring')
    try:
        str_key = bytes(key_bytes).decode('utf-8')
        return str_key, end_of_key
    except Exception:
            raise BsonBadKeyDataError('Имя строки не декодируется в utf-8')


def _decode_element(keys: tp.Any, data: bytes, ind: int, int32_size_document: int,\
                    python_only: bool, keep_types: bool) -> tuple[str, tp.Any, int, bool]:
    global metadata_inter
    TYPE_OF_DATA: int = data[ind]
    str_key, ind = _decode_cstring(data, ind + 1)
    decoded_result: tp.Any = None
    flag = False
    if str_key in keys and str_key != '__metadata__':
        raise BsonRepeatedKeyDataError('Ключ уже встречался')
    if TYPE_OF_DATA in [2, 4, 3, 18, 16, 9, 5, 8, 1, 10]:
        flag = True
        decoded_result = None
    if python_only and TYPE_OF_DATA not in [2, 4, 3, 18, 16, 9, 5, 8, 1, 10]:
        raise BsonInvalidElementTypeError('Тип элемента не поддерживается')
    if TYPE_OF_DATA not in ([*list(range(1, 20)), -1, 127, 255]):
        raise BsonInvalidElementTypeError('what the type')
    ind += 1
    if TYPE_OF_DATA == 2:
        decoded_result, ind = _decode_string(data, ind, int32_size_document)

    elif TYPE_OF_DATA == 1:
        slice_to_convert: list[int] = []
        for j in range(8):
            slice_to_convert.append(data[ind])
            ind += 1
        decoded_result, = struct.unpack('d', bytes(slice_to_convert))
        ind -= 1

    elif TYPE_OF_DATA == 8:
        if data[ind] == 0:
            decoded_result = False
        else:
            decoded_result = True
    elif TYPE_OF_DATA == 5:
        size_of_bytes, = struct.unpack("<i", bytes(data[ind:ind + 4]))
        tmp_bytes = []
        ###subtype checking
        if python_only and data[ind + 4] != 0 and not (str_key == '__metadata__' and data[ind + 4] == 128):
            raise BsonInvalidBinarySubtypeError("Данный subtype не может быть порожден")
        if not (0 <= data[ind + 4] <= 9 or 128 <= data[ind + 4] <= 255):
            raise BsonInvalidBinarySubtypeError("check subtype")

        j = ind + 5
        for t in range(size_of_bytes):
            tmp_bytes.append(data[j])
            j += 1
        decoded_result = bytes(tmp_bytes)
        if 1 <= data[ind + 4] <= 9 or 128 <= data[ind + 4] <= 255:
            flag = False
        ###METADATA
        if str_key == '__metadata__' and data[ind + 4] == 128 and keep_types:
            flag = False
            metadata: str = decoded_result.decode('utf-8')
            metadata_inter = metadata.split(':')
        ############
        ind = j - 1
    elif TYPE_OF_DATA == 9:
        ms, = struct.unpack("<q", bytes(data[ind:ind + 8]))
        decoded_result = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        ind += 7
    elif TYPE_OF_DATA == 16:
        int32_bytes, = struct.unpack("<i", bytes(data[ind:ind + 4]))
        decoded_result = int32_bytes
        ind += 3
    elif TYPE_OF_DATA == 18:
        int64_bytes, = struct.unpack("<q", bytes(data[ind:ind + 8]))
        decoded_result = int64_bytes
        ind += 7
    elif TYPE_OF_DATA == 3:
        size_of_document, = struct.unpack("<i", bytes(data[ind:ind + 4]))
        decoded_result = unmarshal(data[ind:ind + size_of_document], python_only, keep_types)
        ind += size_of_document - 1
    elif TYPE_OF_DATA == 4:
        size_of_document, = struct.unpack("<i", bytes(data[ind:ind + 4]))
        tmp_dict: dict[tp.Any, tp.Any] = unmarshal(data[ind:ind + size_of_document], python_only, keep_types)
        for check_key in tmp_dict.keys():
            if not check_key.isdigit() or (len(check_key) > 1 and check_key[0] == '0'):
                raise BsonBadArrayIndexError('Ошибка в индексах Array')
        max_key: int = -1
        if tmp_dict.keys():
            max_key = max(list(map(int, tmp_dict.keys())))
        if python_only:
            for i in range(0, max_key + 1):
                if str(i) not in tmp_dict.keys():
                    raise BsonInvalidArrayError('У Array отсутствуют индексы, что невозможно при текущей реализации')
        decoded_result = [tmp_dict[str(x)] if str(x) in tmp_dict.keys() else None for x in range(0, max_key + 1)]
        ind += size_of_document - 1
    elif TYPE_OF_DATA == 10:
        decoded_result = None
        if ind == len(data):
            raise BsonBrokenDataError('Потерялся 0')
        ind -= 1
    ###other types

    ###maybe check in the future
    elif TYPE_OF_DATA == 6:
        ind -= 1

    elif TYPE_OF_DATA == 7:
        ind += 11
    elif TYPE_OF_DATA == 11:
        try:
            regex_check, ind = _decode_cstring(data, ind)
        except Exception:
            raise BsonBadStringDataError('ошибка в cstring')
        ind += 1
        try:
            regex_check, ind = _decode_cstring(data, ind)
        except Exception:
            raise BsonBadStringDataError('ошибка в cstring')


    ######CHECK THE STRING
    elif TYPE_OF_DATA == 12 or TYPE_OF_DATA == 13 or TYPE_OF_DATA == 14:
        not_res, ind = _decode_string(data, ind, int32_size_document)
        if TYPE_OF_DATA == 12:
            ind += 12
    ######CHECK THE STRING
    elif TYPE_OF_DATA == 15:
        print(ind)
        size_of_code, = struct.unpack('<i', bytes(data[ind:ind + 4]))
        ind += 4 + size_of_code
        size_of_scope, = struct.unpack('<i', bytes(data[ind:ind + 4]))
        unmarshal(data[ind: ind + size_of_scope], python_only, keep_types)
        ind += size_of_scope - 1

    elif TYPE_OF_DATA == 17:
        ind += 7
    elif TYPE_OF_DATA == 19:
        ind += 15
    elif TYPE_OF_DATA == -1:
        ind -= 1
    elif 127 == TYPE_OF_DATA or TYPE_OF_DATA == 255:
        ind -= 1
    return str_key, decoded_result, ind, flag

def unmarshal(data: bytes, python_only: bool = False, keep_types: bool = False) -> dict[tp.Any, tp.Any]:
    global metadata_inter
    ###size check
    if len(data) < 4:
        raise BsonBrokenDataError('hmmm, you have a problem with bytes size')

    int32_size_document, = struct.unpack('<I', bytes(list(data)[0:4]))

    if int32_size_document < 4:
        raise BsonIncorrectSizeError('it`s unreal')
    if int32_size_document < len(data):
        raise BsonTooManyDataError('unreal again')
    if int32_size_document > len(data):
        raise BsonNotEnoughDataError('too unreal')
    ############

    if data[-1] != 0:
        raise BsonBrokenDataError('where is end zero')

    result: dict[tp.Any, tp.Any] = {}
    ###if empty
    if list(data) == [5, 0, 0, 0, 0]:
        return result
    ###other way
    ind: int = 4
    while ind < len(data):
        if ind == len(list(data)) - 1:
            if list(data)[ind] == 0:
                break
            else:
                raise BsonBrokenDataError('Отсутсвует ноль в конце документа')

        name_key, dec_data, ind, flag = _decode_element(result.keys(), data, ind,
                                                        int32_size_document, python_only, keep_types)

        if flag:
            result[name_key] = dec_data

        if ind >= len(data):
            raise BsonBrokenDataError('error with size')

        ind += 1
    meta_ind: int = 0
    if keep_types and metadata_inter:
        for _key in result:
            print(metadata_inter)
            if metadata_inter[meta_ind] == 'tuple' and isinstance(result[_key], list):
                result[_key] = tuple(result[_key])
            if metadata_inter[meta_ind] == 'bytearray' and isinstance(result[_key], bytes):
                result[_key] = bytearray(result[_key])

            meta_ind += 1
        metadata_inter = []
    return {key: result[key] for key in result}

