#!/usr/bin/env python
from itertools import chain
import os.path as osp
from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto, FieldDescriptorProto as FProto

from uprotobuf import enum, FieldType

def traverse(proto_file):
    def _traverse(package, items):
        for item in items:
            yield item,package

            if isinstance(item, DescriptorProto):
                for enum in item.enum_type:
                    yield enum,package

                for nested in item.nested_type:
                    nested_package=package+item.name
                    for nested_item in _traverse(nested, nested_package):
                        yield nested_item, nested_package
    return chain(
        _traverse(proto_file.package, proto_file.enum_type),
        _traverse(proto_file.package, proto_file.message_type)
    )

def getType(field_type):
    if field_type==FProto.TYPE_BOOL: type="WireType.Varint"; subType="VarintSubType.Bool"
    elif field_type==FProto.TYPE_BYTES: type="WireType.Length"; subType="LengthSubType.Bytes"
    elif field_type==FProto.TYPE_DOUBLE: type="WireType.Bit64"; subType="FixedSubType.Double"
    elif field_type==FProto.TYPE_ENUM: type="WireType.Varint"; subType="VarintSubType.Enum"
    elif field_type==FProto.TYPE_FIXED32: type="WireType.Bit32"; subType="FixedSubType.Fixed32"
    elif field_type==FProto.TYPE_FIXED64: type="WireType.Bit64"; subType="FixedSubType.Fixed64"
    elif field_type==FProto.TYPE_FLOAT: type="WireType.Bit32"; subType="FixedSubType.Float"
    elif field_type==FProto.TYPE_GROUP: type="WireType.Length"; subType="LengthSubType.Group"
    elif field_type==FProto.TYPE_INT32: type="WireType.Varint"; subType="VarintSubType.Int32"
    elif field_type==FProto.TYPE_INT64: type="WireType.Varint"; subType="VarintSubType.Int64"
    elif field_type==FProto.TYPE_MESSAGE: type="WireType.Length"; subType="LengthSubType.Message"
    elif field_type==FProto.TYPE_SFIXED32: type="WireType.Bit32"; subType="FixedSubType.SignedFixed32"
    elif field_type==FProto.TYPE_SFIXED64: type="WireType.Bit64"; subType="FixedSubType.SignedFixed64"
    elif field_type==FProto.TYPE_SINT32: type="WireType.Varint"; subType="VarintSubType.SInt32"
    elif field_type==FProto.TYPE_SINT64: type="WireType.Varint"; subType="VarintSubType.SInt64"
    elif field_type==FProto.TYPE_STRING: type="WireType.Length"; subType="LengthSubType.String"
    elif field_type==FProto.TYPE_UINT32: type="WireType.Varint"; subType="VarintSubType.UInt32"
    elif field_type==FProto.TYPE_UINT64: type="WireType.Varint"; subType="VarintSubType.UInt64"
    else: raise Exception()
    return type,subType

def getFieldType(field_type):
    assert FieldType.isValid(field_type)
    name=FieldType.reverse_mapping[field_type]
    return "FieldType.{}".format(name)

def generateCode(request, response):
    for proto_file in request.proto_file:
        output="from uprotobuf import *\n\n"

        enums=""
        fields=""

        for item,package in traverse(proto_file):
            if isinstance(item, DescriptorProto):
                fields+="\nclass {}Message(Message):\n".format(item.name.capitalize())
                fields+="    _proto_fields=[\n"

                for field in item.field:
                    type,subType=getType(field.type)

                    fields+="        dict(name='{}', type={}, subType={}, fieldType={}, id={}".format(
                        field.name,
                        type,
                        subType,
                        getFieldType(field.label),
                        field.number
                    )
                    if field.type==FProto.TYPE_ENUM: 
                        enum_name=field.type_name.split('.')[-1].capitalize()
                        fields+=", enum={}".format(enum_name)
                    fields+="),\n"

                    # fields+="        # Label: {}, Default Value: {}, Options: {}\n".format(
                    #     field.label, # FProto.LABEL_OPTIONAL, FProto.LABEL_REPEATED, FProto.LABEL_REQUIRED
                    #     field.default_value,
                    #     field.options,
                    # )

                fields+="    ]\n"

            elif isinstance(item, EnumDescriptorProto):
                enums+="\n{}=enum(\n".format(item.name.capitalize())
                for value in item.value:
                    enums+='    {}={},\n'.format(value.name, value.number)
                enums+=")\n"

        output+=enums+fields
        f=response.file.add()
        f.name="{}_upb2.py".format(osp.splitext(proto_file.name)[0])
        f.content=output 

if __name__=="__main__":
    from sys import stdin, stdout

    data=stdin.buffer.read()
    request=plugin.CodeGeneratorRequest()
    request.ParseFromString(data)
    response=plugin.CodeGeneratorResponse()
    generateCode(request, response)
    output=response.SerializeToString()
    stdout.buffer.write(output)
