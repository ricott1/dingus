# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dingus/codec/transaction.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1e\x64ingus/codec/transaction.proto\"\x87\x01\n\x0bTransaction\x12\x0e\n\x06module\x18\x01 \x02(\t\x12\x0f\n\x07\x63ommand\x18\x02 \x02(\t\x12\r\n\x05nonce\x18\x03 \x02(\x04\x12\x0b\n\x03\x66\x65\x65\x18\x04 \x02(\x04\x12\x17\n\x0fsenderPublicKey\x18\x05 \x02(\x0c\x12\x0e\n\x06params\x18\x06 \x02(\x0c\x12\x12\n\nsignatures\x18\x07 \x03(\x0c')



_TRANSACTION = DESCRIPTOR.message_types_by_name['Transaction']
Transaction = _reflection.GeneratedProtocolMessageType('Transaction', (_message.Message,), {
  'DESCRIPTOR' : _TRANSACTION,
  '__module__' : 'dingus.codec.transaction_pb2'
  # @@protoc_insertion_point(class_scope:Transaction)
  })
_sym_db.RegisterMessage(Transaction)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _TRANSACTION._serialized_start=35
  _TRANSACTION._serialized_end=170
# @@protoc_insertion_point(module_scope)
