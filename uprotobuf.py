try: import ustruct as struct
except ImportError: import struct

class UnknownTypeException(Exception): pass
class ValueNotSetException(Exception): pass

class WireType(object):
    Invalid=-1
    Varint=0
    Bit64=1
    Length=2
    Bit32=5

    @classmethod
    def isValid(cls, type):
        return type in (cls.Varint, cls.Bit64, cls.Length, cls.Bit32)

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

class Varint(VarType):
    Int32=1
    Int64=2
    UInt32=3
    UInt64=4
    SInt32=5
    SInt64=6
    Bool=7
    Enum=8

    @staticmethod
    def type(): return WireType.Varint

    def setData(self, data):
        if self._data==data: return
        self._data=data

        self._value=0
        for i,d in enumerate(self._data):
            self._value|=(d&0x7f)<<(i*7)

class Length(VarType):
    String=1
    Message=2

    @staticmethod
    def type(): return WireType.Length

    def setData(self, data):
        if self._data==data: return
        self._data=data

        if self._subType==self.String: self._value=self._data.decode('utf8')

class Fixed(VarType):
    Fixed64=1
    SignedFixed64=2
    Double=3
    Fixed32=4
    SignedFixed32=5
    Float=6

    def __init__(self, id=None, data=None, subType=-1):
        super().__init__(id,data,subType)
        if subType==self.Float: self._fmt='<f'
        elif subType==self.Double: self._fmt='<d'

    def type(self):
        if self._subType in (self.Fixed64, self.SignedFixed64, self.Double):
            return WireType.Bit64
        else: return WireType.Bit32

    def setData(self, data):
        if self._data==data: return
        self._data=data

        if self._subType in (self.Float,self.Double):
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

class Test1Message(Message):
    _proto_fields=[
        dict(name="a", type=WireType.Varint, subType=Varint.Int32, id=1),
        dict(name="b", type=WireType.Length, subType=Length.String, id=2),
        dict(name="c", type=WireType.Varint, subType=Varint.Int64, id=4),
        dict(name="d", type=WireType.Bit32, subType=Fixed.Float, id=5),
        dict(name="e", type=WireType.Bit32, subType=Fixed.Double, id=6),
    ]

if __name__=="__main__":
    m=Test1Message()
    
    print("Simple\n======")
    msg=b"\x08\x96\x01"
    m.parse(msg)
    for k,v in m.items(): print(k,v)
    print()

    print("String\n======")
    msg=b'\x08\x96\x01\x12\x07testing'
    m.parse(msg)
    for k,v in m.items(): print(k,v)
    print()

    print("Complex\n=======")
    msg=b'\x08\x96\x01\x12\x07testing \xff\xff\xff\xff\xff\xff\xff\xff\xff\x01-\x00\x00\x80?1\x00\x00\x00\x00\x00\x00\x00@'
    m.parse(msg)
    for k,v in m.items(): print(k,v)
    print()
    
    m.a=120
    print(m.a)