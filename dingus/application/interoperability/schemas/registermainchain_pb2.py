# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: registermainchain.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17registermainchain.proto\"\xd0\x01\n\x11RegisterMainchain\x12\x12\n\nownChainID\x18\x01 \x02(\x0c\x12\x0f\n\x07ownName\x18\x02 \x02(\t\x12\x43\n\x13mainchainValidators\x18\x03 \x03(\x0b\x32&.RegisterMainchain_MainchainValidators\x12%\n\x1dmainchainCertificateThreshold\x18\x04 \x02(\x04\x12\x11\n\tsignature\x18\x05 \x02(\x0c\x12\x17\n\x0f\x61ggregationBits\x18\x06 \x02(\x0c\"J\n%RegisterMainchain_MainchainValidators\x12\x0e\n\x06\x62lsKey\x18\x01 \x02(\x0c\x12\x11\n\tbftWeight\x18\x02 \x02(\x04')



_REGISTERMAINCHAIN = DESCRIPTOR.message_types_by_name['RegisterMainchain']
_REGISTERMAINCHAIN_MAINCHAINVALIDATORS = DESCRIPTOR.message_types_by_name['RegisterMainchain_MainchainValidators']
RegisterMainchain = _reflection.GeneratedProtocolMessageType('RegisterMainchain', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERMAINCHAIN,
  '__module__' : 'registermainchain_pb2'
  # @@protoc_insertion_point(class_scope:RegisterMainchain)
  })
_sym_db.RegisterMessage(RegisterMainchain)

RegisterMainchain_MainchainValidators = _reflection.GeneratedProtocolMessageType('RegisterMainchain_MainchainValidators', (_message.Message,), {
  'DESCRIPTOR' : _REGISTERMAINCHAIN_MAINCHAINVALIDATORS,
  '__module__' : 'registermainchain_pb2'
  # @@protoc_insertion_point(class_scope:RegisterMainchain_MainchainValidators)
  })
_sym_db.RegisterMessage(RegisterMainchain_MainchainValidators)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _REGISTERMAINCHAIN._serialized_start=28
  _REGISTERMAINCHAIN._serialized_end=236
  _REGISTERMAINCHAIN_MAINCHAINVALIDATORS._serialized_start=238
  _REGISTERMAINCHAIN_MAINCHAINVALIDATORS._serialized_end=312
# @@protoc_insertion_point(module_scope)
