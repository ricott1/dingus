# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: transfer.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0etransfer.proto\"S\n\x08Transfer\x12\x0f\n\x07tokenID\x18\x01 \x02(\x0c\x12\x0e\n\x06\x61mount\x18\x02 \x02(\x04\x12\x18\n\x10recipientAddress\x18\x03 \x02(\x0c\x12\x0c\n\x04\x64\x61ta\x18\x04 \x02(\t')



_TRANSFER = DESCRIPTOR.message_types_by_name['Transfer']
Transfer = _reflection.GeneratedProtocolMessageType('Transfer', (_message.Message,), {
  'DESCRIPTOR' : _TRANSFER,
  '__module__' : 'transfer_pb2'
  # @@protoc_insertion_point(class_scope:Transfer)
  })
_sym_db.RegisterMessage(Transfer)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _TRANSFER._serialized_start=18
  _TRANSFER._serialized_end=101
# @@protoc_insertion_point(module_scope)