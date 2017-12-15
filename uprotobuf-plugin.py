#!/home/rob/Development/protobuf/env/bin/python
from itertools import chain
import os.path as osp
from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto, FieldDescriptorProto as FProto

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
    if field_type==FProto.TYPE_BOOL: type="WireType.Varint"; subType="Varint.Bool"
    elif field_type==FProto.TYPE_BYTES: type="WireType.Length"; subType="Length.Bytes"
    elif field_type==FProto.TYPE_DOUBLE: type="WireType.Bit64"; subType="Fixed.Double"
    elif field_type==FProto.TYPE_ENUM: type="WireType.Varint"; subType="Varint.Enum"
    elif field_type==FProto.TYPE_FIXED32: type="WireType.Bit32"; subType="Fixed.Fixed32"
    elif field_type==FProto.TYPE_FIXED64: type="WireType.Bit64"; subType="Fixed.Fixed64"
    elif field_type==FProto.TYPE_FLOAT: type="WireType.Bit32"; subType="Fixed.Float"
    elif field_type==FProto.TYPE_GROUP: type="WireType.Length"; subType="Length.Group"
    elif field_type==FProto.TYPE_INT32: type="WireType.Varint"; subType="Varint.Int32"
    elif field_type==FProto.TYPE_INT64: type="WireType.Varint"; subType="Varint.Int64"
    elif field_type==FProto.TYPE_MESSAGE: type="WireType.Length"; subType="Length.Message"
    elif field_type==FProto.TYPE_SFIXED32: type="WireType.Bit32"; subType="Fixed.SignedFixed32"
    elif field_type==FProto.TYPE_SFIXED64: type="WireType.Bit64"; subType="Fixed.SignedFIxed64"
    elif field_type==FProto.TYPE_SINT32: type="WireType.Varint"; subType="Varint.SInt32"
    elif field_type==FProto.TYPE_SINT64: type="WireType.Varint"; subType="Varint.SInt64"
    elif field_type==FProto.TYPE_STRING: type="WireType.Length"; subType="Length.String"
    elif field_type==FProto.TYPE_UINT32: type="WireType.Varint"; subType="Varint.UInt32"
    elif field_type==FProto.TYPE_UINT64: type="WireType.Varint"; subType="Varint.UInt64"
    else: raise Exception()
    return type,subType

def generateCode(request, response):
    for proto_file in request.proto_file:
        output="from uprotobuf import Message, WireType, Varint, Fixed, Length\n\n"

        for item,package in traverse(proto_file):
            if isinstance(item, DescriptorProto):
                output+="class {}Message(Message):\n".format(item.name.capitalize())
                output+="    _proto_fields=[\n"

                for field in item.field:

                    type,subType=getType(field.type)

                    # Need to hance field.default_value and field.options and field.label (required/optional/repeated?)
                    output+="        dict(name='{}', type={}, subType={}, id={}),\n".format(
                        field.name,
                        type,
                        subType,
                        field.number
                    )
                    output+="        # Label: {}, Default Value: {}, Options: {}\n".format(
                        field.label, # FProto.LABEL_OPTIONAL, FProto.LABEL_REPEATED, FProto.LABEL_REQUIRED
                        field.default_value,
                        field.options
                    )

                output+="    ]\n"

            elif isinstance(item, EnumDescriptorProto):
                # Need to write an Enum class for upy...
                # '''class <item.name>(Enum):'''
                #     for value in item.value:
                #     '''<value.name>=<value.number>'''
                pass

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
