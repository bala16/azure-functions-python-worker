import abc
import enum
import json
import typing

from . import protos


class Binding(str, enum.Enum):
    """Supported binding types."""

    blob = 'blob'
    blobTrigger = 'blobTrigger'
    http = 'http'
    httpTrigger = 'httpTrigger'
    timerTrigger = 'timerTrigger'
    queue = 'queue'
    queueTrigger = 'queueTrigger'

    def is_trigger(self):
        return self.endswith('Trigger')


class _ConverterMeta(abc.ABCMeta):

    _check_py_type: typing.Mapping[Binding, typing.Callable[[type], bool]] = {}
    _from_proto: typing.Mapping[Binding, typing.Callable] = {}
    _to_proto: typing.Mapping[Binding, typing.Callable] = {}

    def __new__(mcls, name, bases, dct, *, binding: typing.Optional[Binding]):
        cls = super().__new__(mcls, name, bases, dct)
        if binding is None:
            return cls

        if binding in mcls._check_py_type:
            raise RuntimeError(
                f'cannot register a converter for {binding} binding: '
                f'another converter has already been registered')

        mcls._check_py_type[binding] = getattr(cls, 'check_python_type')

        if issubclass(cls, InConverter):
            assert binding not in mcls._from_proto
            mcls._from_proto[binding] = getattr(cls, 'from_proto')

        if issubclass(cls, OutConverter):
            assert binding not in mcls._to_proto
            mcls._to_proto[binding] = getattr(cls, 'to_proto')

        return cls


class _BaseConverter(metaclass=_ConverterMeta, binding=None):

    @abc.abstractclassmethod
    def check_python_type(cls, pytype: type) -> bool:
        pass

    @classmethod
    def _decode_scalar_typed_data(
            cls, data: typing.Optional[protos.TypedData]) -> typing.Any:
        if data is None:
            return None

        data_type = data.WhichOneof('data')
        if data_type == 'json':
            result = json.loads(data.json)
        elif data_type == 'string':
            result = data.string
        elif data_type == 'bytes':
            result = data.bytes
        else:
            raise NotImplementedError(
                f'unsupported type of field in trigger metadata: {data_type}')

        return result


class InConverter(_BaseConverter, binding=None):

    @abc.abstractclassmethod
    def from_proto(cls, data: protos.TypedData,
                   trigger_metadata) -> typing.Any:
        pass


class OutConverter(_BaseConverter, binding=None):

    @abc.abstractclassmethod
    def to_proto(cls, obj: typing.Any) -> protos.TypedData:
        pass


def check_bind_type_matches_py_type(
        binding: Binding, pytype: type) -> bool:

    try:
        checker = _ConverterMeta._check_py_type[binding]
    except KeyError:
        raise TypeError(
            f'bind type {binding} does not have '
            'a corresponding Python type') from None

    return checker(pytype)


def from_incoming_proto(
        binding: Binding, val: protos.TypedData,
        trigger_metadata: typing.Optional[typing.Dict[str, protos.TypedData]])\
        -> typing.Any:
    converter = _ConverterMeta._from_proto.get(binding)

    try:
        try:
            converter = _ConverterMeta._from_proto[binding]
        except KeyError:
            raise NotImplementedError
        else:
            return converter(val, trigger_metadata)
    except NotImplementedError:
        # Either there's no converter or a converter has failed.
        dt = val.WhichOneof('data')

        raise TypeError(
            f'unable to decode incoming TypedData: '
            f'unsupported combination of TypedData field {dt!r} '
            f'and expected binding type {binding}')


def to_outgoing_proto(binding: Binding, obj: typing.Any) -> protos.TypedData:
    converter = _ConverterMeta._to_proto.get(binding)

    try:
        try:
            converter = _ConverterMeta._to_proto[binding]
        except KeyError:
            raise NotImplementedError
        else:
            return converter(obj)
    except NotImplementedError:
        # Either there's no converter or a converter has failed.
        raise TypeError(
            f'unable to encode outgoing TypedData: '
            f'unsupported type "{binding}" for '
            f'Python type "{type(obj).__name__}"')


from . import type_converters  # NoQA