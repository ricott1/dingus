# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: registerkeys.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12registerkeys.proto\"O\n\x0cRegisterKeys\x12\x0e\n\x06\x62lsKey\x18\x01 \x02(\x0c\x12\x19\n\x11proofOfPossession\x18\x02 \x02(\x0c\x12\x14\n\x0cgeneratorKey\x18\x03 \x02(\x0c')



_REGISTERKEYS = DESCRIPTOR.message_types_by_name['RegisterKeys']
RegisterKeys = _reflection.GeneratedProtocolMessageType('RegisterKeys', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERKEYS,
  '__module__' : 'registerkeys_pb2'
  # @@protoc_insertion_point(class_scope:RegisterKeys)
  })
_sym_db.RegisterMessage(RegisterKeys)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _REGISTERKEYS._serialized_start=22
  _REGISTERKEYS._serialized_end=101
# @@protoc_insertion_point(module_scope)