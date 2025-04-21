class BsonError(ValueError):
    pass
class MapperConfigError(ValueError):
    pass
class BsonMarshalError(BsonError):
    pass
class BsonUnsupportedObjectError(BsonMarshalError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonUnsupportedKeyError(BsonMarshalError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonKeyWithZeroByteError(BsonUnsupportedKeyError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

###FOR BIG INPUT###
class BsonInputTooBigError(BsonMarshalError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonIntegerTooBigError(BsonInputTooBigError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonStringTooBigError(BsonInputTooBigError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonBinaryTooBigError(BsonInputTooBigError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonDocumentTooBigError(BsonInputTooBigError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
##################

class BsonCycleDetectedError(BsonMarshalError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class BsonUnmarshalError(BsonError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonBrokenDataError(BsonUnmarshalError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonIncorrectSizeError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonTooManyDataError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonNotEnoughDataError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonInvalidElementTypeError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonInvalidStringError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonStringSizeError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class BsonInconsistentStringSizeError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonBadStringDataError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonBadKeyDataError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonRepeatedKeyDataError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonBadArrayIndexError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonInvalidBinarySubtypeError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
class BsonInvalidArrayError(BsonBrokenDataError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class MapperUnsupportedOptionError(MapperConfigError):
    def __init__(self, message: str) -> None:
        super().__init__(message)