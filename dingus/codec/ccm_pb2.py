# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ccm.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tccm.proto\"\x9e\x01\n\x03\x43\x43M\x12\x0e\n\x06module\x18\x01 \x02(\t\x12\x19\n\x11\x63rossChainCommand\x18\x02 \x02(\t\x12\r\n\x05nonce\x18\x03 \x02(\x04\x12\x0b\n\x03\x66\x65\x65\x18\x04 \x02(\x04\x12\x16\n\x0esendingChainID\x18\x05 \x02(\x0c\x12\x18\n\x10receivingChainID\x18\x06 \x02(\x0c\x12\x0e\n\x06params\x18\x07 \x02(\x0c\x12\x0e\n\x06status\x18\x08 \x02(\r\"H\n\x0cRegistration\x12\x0c\n\x04name\x18\x01 \x02(\t\x12\x0f\n\x07\x63hainID\x18\x02 \x02(\x0c\x12\x19\n\x11messageFeeTokenID\x18\x03 \x02(\x0c')



_CCM = DESCRIPTOR.message_types_by_name['CCM']
_REGISTRATION = DESCRIPTOR.message_types_by_name['Registration']
CCM = _reflection.GeneratedProtocolMessageType('CCM', (_message.Message,), {
  'DESCRIPTOR' : _CCM,
  '__module__' : 'ccm_pb2'
  # @@protoc_insertion_point(class_scope:CCM)
  })
_sym_db.RegisterMessage(CCM)

Registration = _reflection.GeneratedProtocolMessageType('Registration', (_message.Message,), {
  'DESCRIPTOR' : _REGISTRATION,
  '__module__' : 'ccm_pb2'
  # @@protoc_insertion_point(class_scope:Registration)
  })
_sym_db.RegisterMessage(Registration)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CCM._serialized_start=14
  _CCM._serialized_end=172
  _REGISTRATION._serialized_start=174
  _REGISTRATION._serialized_end=246
# @@protoc_insertion_point(module_scope)