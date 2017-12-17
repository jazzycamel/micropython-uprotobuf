try: import ustruct as struct
except ImportError: import struct

class UnknownTypeException(Exception): pass
class ValueNotSetException(Exception): pass

def enum(*sequential, **named):
    def isValid(cls, type):
        return type in cls.reverse_mapping

    enums=dict(((x,i) for i,x in enumerate(sequential)), **named)   
    enums['reverse_mapping']=dict((value,key) for key,value in enums.items())
    enums['isValid']=classmethod(isValid)
    return type('Enum', (object,), enums)

WireType=enum(Invalid=-1, Varint=0, Bit64=1, Length=2, Bit32=5)

class VarType(object):
    def __init__(self, id=None, data=None, subType=-1):
        self._id=id
        self._data=data
        self._value=None
        self._subType=subType

    @staticmethod
    def type(): return WireType.Invalid

    def data(self): return self._data

    def setData(self, data):
        if self._data==data: return 
        self._data=data

    def value(self): return self._value

    def setValue(self, value):
        if self._value==value: return
        self._value=value       

    def __repr__(self):
        return "{}({}: {})".format(self.__class__.__name__, self._id, self._value)

    @staticmethod
    def encodeZigZag(n, bits=32): return (n<<1)^(n>>(bits-1))

    @staticmethod
    def decodeZigZag(n): return (n>>1)^-(n&1)

VarintSubType=enum(
    Int32=1,
    Int64=2,
    UInt32=3,
    UInt64=4,
    SInt32=5,
    SInt64=6,
    Bool=7,
    Enum=8,
)

class Varint(VarType):
    @staticmethod
    def type(): return WireType.Varint

    def setData(self, data):
        if self._data==data: return
        self._data=data

        self._value=0
        for i,d in enumerate(self._data):
            self._value|=(d&0x7f)<<(i*7)

LengthSubType=enum(
    String=1,
    Message=2,
    Group=3,
    Bytes=4,
)

class Length(VarType):
    @staticmethod
    def type(): return WireType.Length

    def setData(self, data):
        if self._data==data: return
        self._data=data

        if self._subType==LengthSubType.String: self._value=self._data.decode('utf8')

FixedSubType=enum(
    Fixed64=1,
    SignedFixed64=2,
    Double=3,
    Fixed32=4,
    SignedFixed32=5,
    Float=6,
)

class Fixed(VarType):
    def __init__(self, id=None, data=None, subType=-1):
        super().__init__(id,data,subType)
        if subType==FixedSubType.Float: self._fmt='<f'
        elif subType==FixedSubType.Double: self._fmt='<d'

    def type(self):
        if self._subType in (FixedSubType.Fixed64, FixedSubType.SignedFixed64, FixedSubType.Double):
            return WireType.Bit64
        else: return WireType.Bit32

    def setData(self, data):
        if self._data==data: return
        self._data=data

        if self._subType in (FixedSubType.Float, FixedSubType.Double):
            self._value=self.decodeFloat(self._data, self._fmt)

    @staticmethod
    def encodeFloat(n, fmt='<f'): return struct.pack(fmt,n)

    @staticmethod
    def decodeFloat(n, fmt='<f'): return struct.unpack(fmt,n)[0]

class Message(object):
    def __init__(self):

        self._fieldsLUT={}
        self._fields={}
        for field in self._proto_fields:
            if field['type']==WireType.Varint: clazz=Varint
            elif field['type']==WireType.Length: clazz=Length
            elif field['type'] in (WireType.Bit32, WireType.Bit64): clazz=Fixed
            else: raise UnknownTypeException

            self._fieldsLUT[field['id']]=field['name']
            self._fields[field['name']]=clazz(id=field['id'], subType=field['subType'])
        self.fields=self._fields

    def __getattr__(self, name):
       return self.fields[name]

    def __setattr__(self, name, value):
        if '_fields' in self.__dict__:
            if name in self.__dict__['_fields']:
                self.__dict__['_fields'][name].setValue(value)
                return
        super().__setattr__(name,value)

    def __iter__(self):
       return iter(self._fields.keys())

    def keys(self): return self._fields.keys()

    def values(self): return self._fields.values()

    def items(self): return self._fields.items()

    def parse(self, msg):
        i=0
        while i<len(msg):
            byte=msg[i]           
            type=byte&0x7
            if not WireType.isValid(type):
                i+=1
                continue

            id=byte>>3
            name=self._fieldsLUT[id]
            data=None
            if type==WireType.Varint:
                data=[]
                while True:
                    i+=1
                    data.append(msg[i])
                    if not msg[i]&0x80: break
                i+=1

            elif type in (WireType.Bit32, WireType.Bit64, WireType.Length):
                if type==WireType.Length:
                    i+=1
                    length=int(msg[i])
                else: length=4 if type==WireType.Bit32 else 8

                i+=1
                data=msg[i:i+length]
                i+=length

            else: raise UnknownTypeException

            if name not in self._fields: continue
            self._fields[name].setData(data)
