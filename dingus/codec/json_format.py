# Protocol Buffers - Google's data interchange format
# Copyright 2008 Google Inc.  All rights reserved.
# https://developers.google.com/protocol-buffers/
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Contains routines for printing protocol messages in JSON format.
Only modification is returning hex encoding of bytes type,
rather than base 64.

Simple usage example:

  # Create a proto object and serialize it to a json format string.
  message = my_proto_pb2.MyMessage(foo='bar')
  json_string = json_format.MessageToJson(message)

  # Parse a json format string to proto object.
  message = json_format.Parse(json_string, my_proto_pb2.MyMessage())
"""

__author__ = "jieluo@google.com (Jie Luo)"

from collections import OrderedDict
import json
import math
from operator import methodcaller
import re

from google.protobuf.internal import type_checkers
from google.protobuf import descriptor
from google.protobuf import symbol_database

_INT64_TYPES = frozenset(
    [
        descriptor.FieldDescriptor.CPPTYPE_INT64,
        descriptor.FieldDescriptor.CPPTYPE_UINT64,
    ]
)
_FLOAT_TYPES = frozenset(
    [
        descriptor.FieldDescriptor.CPPTYPE_FLOAT,
        descriptor.FieldDescriptor.CPPTYPE_DOUBLE,
    ]
)
_INFINITY = "Infinity"
_NEG_INFINITY = "-Infinity"
_NAN = "NaN"

class Error(Exception):
    """Top-level module error for json_format."""


class SerializeToJsonError(Error):
    """Thrown if serialization to JSON fails."""


class ParseError(Error):
    """Thrown in case of parsing error."""

def MessageToDict(
    message,
    including_default_value_fields=False,
    preserving_proto_field_name=False,
    use_integers_for_enums=False,
    descriptor_pool=None,
    float_precision=None,
):
    """Converts protobuf message to a dictionary.

    When the dictionary is encoded to JSON, it conforms to proto3 JSON spec.

    Args:
      message: The protocol buffers message instance to serialize.
      including_default_value_fields: If True, singular primitive fields,
          repeated fields, and map fields will always be serialized.  If
          False, only serialize non-empty fields.  Singular message fields
          and oneof fields are not affected by this option.
      preserving_proto_field_name: If True, use the original proto field
          names as defined in the .proto file. If False, convert the field
          names to lowerCamelCase.
      use_integers_for_enums: If true, print integers instead of enum names.
      descriptor_pool: A Descriptor Pool for resolving types. If None use the
          default.
      float_precision: If set, use this to specify float field valid digits.

    Returns:
      A dict representation of the protocol buffer message.
    """
    printer = _Printer(
        including_default_value_fields,
        preserving_proto_field_name,
        use_integers_for_enums,
        descriptor_pool,
        float_precision=float_precision,
    )
    # pylint: disable=protected-access
    return printer._MessageToJsonObject(message)


def _IsMapEntry(field):
    return (
        field.type == descriptor.FieldDescriptor.TYPE_MESSAGE
        and field.message_type.has_options
        and field.message_type.GetOptions().map_entry
    )


class _Printer(object):
    """JSON format printer for protocol message."""

    def __init__(
        self,
        including_default_value_fields=False,
        preserving_proto_field_name=False,
        use_integers_for_enums=False,
        descriptor_pool=None,
        float_precision=None,
    ):
        self.including_default_value_fields = including_default_value_fields
        self.preserving_proto_field_name = preserving_proto_field_name
        self.use_integers_for_enums = use_integers_for_enums
        self.descriptor_pool = descriptor_pool
        if float_precision:
            self.float_format = ".{}g".format(float_precision)
        else:
            self.float_format = None

    def ToJsonString(self, message, indent, sort_keys):
        js = self._MessageToJsonObject(message)
        return json.dumps(js, indent=indent, sort_keys=sort_keys)

    def _MessageToJsonObject(self, message):
        """Converts message to an object according to Proto3 JSON Specification."""
        message_descriptor = message.DESCRIPTOR
        full_name = message_descriptor.full_name
        if _IsWrapperMessage(message_descriptor):
            return self._WrapperMessageToJsonObject(message)
        if full_name in _WKTJSONMETHODS:
            return methodcaller(_WKTJSONMETHODS[full_name][0], message)(self)
        js = {}
        return self._RegularMessageToJsonObject(message, js)

    def _RegularMessageToJsonObject(self, message, js):
        """Converts normal message according to Proto3 JSON Specification."""
        fields = message.ListFields()

        try:
            for field, value in fields:
                if self.preserving_proto_field_name:
                    name = field.name
                else:
                    name = field.json_name
                if _IsMapEntry(field):
                    # Convert a map field.
                    v_field = field.message_type.fields_by_name["value"]
                    js_map = {}
                    for key in value:
                        if isinstance(key, bool):
                            if key:
                                recorded_key = "true"
                            else:
                                recorded_key = "false"
                        else:
                            recorded_key = str(key)
                        js_map[recorded_key] = self._FieldToJsonObject(
                            v_field, value[key]
                        )
                    js[name] = js_map
                elif field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
                    # Convert a repeated field.
                    js[name] = [self._FieldToJsonObject(field, k) for k in value]
                elif field.is_extension:
                    name = "[%s]" % field.full_name
                    js[name] = self._FieldToJsonObject(field, value)
                else:
                    js[name] = self._FieldToJsonObject(field, value)

            # Serialize default value if including_default_value_fields is True.
            if self.including_default_value_fields:
                message_descriptor = message.DESCRIPTOR
                for field in message_descriptor.fields:
                    # Singular message fields and oneof fields will not be affected.
                    if (
                        field.label != descriptor.FieldDescriptor.LABEL_REPEATED
                        and field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_MESSAGE
                    ) or field.containing_oneof:
                        continue
                    if self.preserving_proto_field_name:
                        name = field.name
                    else:
                        name = field.json_name
                    if name in js:
                        # Skip the field which has been serialized already.
                        continue
                    if _IsMapEntry(field):
                        js[name] = {}
                    elif field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
                        js[name] = []
                    else:
                        js[name] = self._FieldToJsonObject(field, field.default_value)

        except ValueError as e:
            raise SerializeToJsonError(
                "Failed to serialize {0} field: {1}.".format(field.name, e)
            )

        return js

    def _FieldToJsonObject(self, field, value):
        """Converts field value according to Proto3 JSON Specification."""
        if field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_MESSAGE:
            return self._MessageToJsonObject(value)
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_ENUM:
            if self.use_integers_for_enums:
                return value
            if field.enum_type.full_name == "google.protobuf.NullValue":
                return None
            enum_value = field.enum_type.values_by_number.get(value, None)
            if enum_value is not None:
                return enum_value.name
            else:
                if field.file.syntax == "proto3":
                    return value
                raise SerializeToJsonError(
                    "Enum field contains an integer value "
                    "which can not mapped to an enum value."
                )
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_STRING:
            if field.type == descriptor.FieldDescriptor.TYPE_BYTES:
                # Use hex Data encoding for bytes
                return value.hex()
            else:
                return value
        elif field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_BOOL:
            return bool(value)
        elif field.cpp_type in _INT64_TYPES:
            return str(value)
        elif field.cpp_type in _FLOAT_TYPES:
            if math.isinf(value):
                if value < 0.0:
                    return _NEG_INFINITY
                else:
                    return _INFINITY
            if math.isnan(value):
                return _NAN
            if field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_FLOAT:
                if self.float_format:
                    return float(format(value, self.float_format))
                else:
                    return type_checkers.ToShortestFloat(value)

        return value

    def _AnyMessageToJsonObject(self, message):
        """Converts Any message according to Proto3 JSON Specification."""
        if not message.ListFields():
            return {}
        # Must print @type first, use OrderedDict instead of {}
        js = OrderedDict()
        type_url = message.type_url
        js["@type"] = type_url
        sub_message = _CreateMessageFromTypeUrl(type_url, self.descriptor_pool)
        sub_message.ParseFromString(message.value)
        message_descriptor = sub_message.DESCRIPTOR
        full_name = message_descriptor.full_name
        if _IsWrapperMessage(message_descriptor):
            js["value"] = self._WrapperMessageToJsonObject(sub_message)
            return js
        if full_name in _WKTJSONMETHODS:
            js["value"] = methodcaller(_WKTJSONMETHODS[full_name][0], sub_message)(self)
            return js
        return self._RegularMessageToJsonObject(sub_message, js)

    def _GenericMessageToJsonObject(self, message):
        """Converts message according to Proto3 JSON Specification."""
        # Duration, Timestamp and FieldMask have ToJsonString method to do the
        # convert. Users can also call the method directly.
        return message.ToJsonString()

    def _ValueMessageToJsonObject(self, message):
        """Converts Value message according to Proto3 JSON Specification."""
        which = message.WhichOneof("kind")
        # If the Value message is not set treat as null_value when serialize
        # to JSON. The parse back result will be different from original message.
        if which is None or which == "null_value":
            return None
        if which == "list_value":
            return self._ListValueMessageToJsonObject(message.list_value)
        if which == "struct_value":
            value = message.struct_value
        else:
            value = getattr(message, which)
        oneof_descriptor = message.DESCRIPTOR.fields_by_name[which]
        return self._FieldToJsonObject(oneof_descriptor, value)

    def _ListValueMessageToJsonObject(self, message):
        """Converts ListValue message according to Proto3 JSON Specification."""
        return [self._ValueMessageToJsonObject(value) for value in message.values]

    def _StructMessageToJsonObject(self, message):
        """Converts Struct message according to Proto3 JSON Specification."""
        fields = message.fields
        ret = {}
        for key in fields:
            ret[key] = self._ValueMessageToJsonObject(fields[key])
        return ret

    def _WrapperMessageToJsonObject(self, message):
        return self._FieldToJsonObject(
            message.DESCRIPTOR.fields_by_name["value"], message.value
        )


def _IsWrapperMessage(message_descriptor):
    return message_descriptor.file.name == "google/protobuf/wrappers.proto"

def _CreateMessageFromTypeUrl(type_url, descriptor_pool):
    """Creates a message from a type URL."""
    db = symbol_database.Default()
    pool = db.pool if descriptor_pool is None else descriptor_pool
    type_name = type_url.split("/")[-1]
    try:
        message_descriptor = pool.FindMessageTypeByName(type_name)
    except KeyError:
        raise TypeError(
            "Can not find message descriptor by type_url: {0}.".format(type_url)
        )
    message_class = db.GetPrototype(message_descriptor)
    return message_class()

_WKTJSONMETHODS = {
    "google.protobuf.Any": ["_AnyMessageToJsonObject", "_ConvertAnyMessage"],
    "google.protobuf.Duration": [
        "_GenericMessageToJsonObject",
        "_ConvertGenericMessage",
    ],
    "google.protobuf.FieldMask": [
        "_GenericMessageToJsonObject",
        "_ConvertGenericMessage",
    ],
    "google.protobuf.ListValue": [
        "_ListValueMessageToJsonObject",
        "_ConvertListValueMessage",
    ],
    "google.protobuf.Struct": ["_StructMessageToJsonObject", "_ConvertStructMessage"],
    "google.protobuf.Timestamp": [
        "_GenericMessageToJsonObject",
        "_ConvertGenericMessage",
    ],
    "google.protobuf.Value": ["_ValueMessageToJsonObject", "_ConvertValueMessage"],
}
