# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sidechainregistrationparams.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!sidechainregistrationparams.proto\"\xb2\x01\n\x1bSidechainRegistrationParams\x12\x0f\n\x07\x63hainID\x18\x01 \x02(\x0c\x12\x0c\n\x04name\x18\x02 \x02(\t\x12M\n\x13sidechainValidators\x18\x03 \x03(\x0b\x32\x30.SidechainRegistrationParams_SidechainValidators\x12%\n\x1dsidechainCertificateThreshold\x18\x04 \x02(\x04\"T\n/SidechainRegistrationParams_SidechainValidators\x12\x0e\n\x06\x62lsKey\x18\x01 \x02(\x0c\x12\x11\n\tbftWeight\x18\x02 \x02(\x04')



_SIDECHAINREGISTRATIONPARAMS = DESCRIPTOR.message_types_by_name['SidechainRegistrationParams']
_SIDECHAINREGISTRATIONPARAMS_SIDECHAINVALIDATORS = DESCRIPTOR.message_types_by_name['SidechainRegistrationParams_SidechainValidators']
SidechainRegistrationParams = _reflection.GeneratedProtocolMessageType('SidechainRegistrationParams', (_message.Message,), {
  'DESCRIPTOR' : _SIDECHAINREGISTRATIONPARAMS,
  '__module__' : 'sidechainregistrationparams_pb2'
  # @@protoc_insertion_point(class_scope:SidechainRegistrationParams)
  })
_sym_db.RegisterMessage(SidechainRegistrationParams)

SidechainRegistrationParams_SidechainValidators = _reflection.GeneratedProtocolMessageType('SidechainRegistrationParams_SidechainValidators', (_message.Message,), {
  'DESCRIPTOR' : _SIDECHAINREGISTRATIONPARAMS_SIDECHAINVALIDATORS,
  '__module__' : 'sidechainregistrationparams_pb2'
  # @@protoc_insertion_point(class_scope:SidechainRegistrationParams_SidechainValidators)
  })
_sym_db.RegisterMessage(SidechainRegistrationParams_SidechainValidators)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SIDECHAINREGISTRATIONPARAMS._serialized_start=38
  _SIDECHAINREGISTRATIONPARAMS._serialized_end=216
  _SIDECHAINREGISTRATIONPARAMS_SIDECHAINVALIDATORS._serialized_start=218
  _SIDECHAINREGISTRATIONPARAMS_SIDECHAINVALIDATORS._serialized_end=302
# @@protoc_insertion_point(module_scope)