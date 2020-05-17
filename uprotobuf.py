try: import ustruct as struct
except ImportError: import struct

class UnknownTypeException(Exception): pass
class ValueNotSetException(Exception): pass

def partial(func, *args, **kwargs):
    def _partial(*more_args, **more_kwargs):
        kw = kwargs.copy()
        kw.update(more_kwargs)
        return func(*(args + more_args), **kw)
    return _partial

def enum(*sequential, **named):
    def isValid(cls, type):
        return type in cls.reverse_mapping

    enums=dict(((x,i) for i,x in enumerate(sequential)), **named)   
    enums['reverse_mapping']=dict((value,key) for key,value in enums.items())
    enums['isValid']=classmethod(isValid)
    return type('Enum', (object,), enums)
    
_MessageRegister = {}
def registerMessage(cls):
    global _MessageRegister
    _MessageRegister[".protobuf.{}".format(cls.__name__).lower()] = cls
    return cls
def getMessageType(name): 
    global _MessageRegister
    key = name+"Message"
    key = key.lower()
    return _MessageRegister[key]
    
def getBytesForId(_id, typ):
    if _id < 0xF:return [(_id<<3)|typ]#we shouldnt get bigger than 0xFF (we shift left 3 bit => 0xF-> 0x78+typ => max 0x7F
    else:
        data =[]
        value = (_id << 3) | typ
        while value >= 0x7f:
            data.append((value&0x7F)|0x80)
            value=value>>7
            data.append(value&0x7F)
        return data

WireType=enum(Invalid=-1, Varint=0, Bit64=1, Length=2, Bit32=5)
FieldType=enum(Invalid=-1, Optional=1, Required=2, Repeated=3)

class VarType(object):
    def __init__(self, id=None, data=None, subType=-1, fieldType=-1, **kwargs):
        self._id=id
        self._data=data
        self._value=[] if fieldType is FieldType.Repeated else None
        self._subType=subType
        self._fieldType=fieldType
        self._mType = kwargs.get("mType","")

    def reset(self):
        self._data=None
        self._value=[] if self._fieldType is FieldType.Repeated else None

    def isValid(self):
        if not self._fieldType==FieldType.Required: return True
        return self._data!=None and self._value not in (None, [])

    @property
    def id(self): return self._id

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
    def __init__(self, id=None, data=None, subType=-1, fieldType=-1, **kwargs):
        super().__init__(id, data, subType, fieldType, **kwargs)

        if subType==VarintSubType.Enum:
            self._enum=kwargs['enum']

    @staticmethod
    def type(): return WireType.Varint

    def setData(self, data):
        if self._data==data: return
        self._data=data

        value=0
        for i,d in enumerate(self._data):
            value|=(d&0x7f)<<(i*7)

        if self._subType in (VarintSubType.SInt32, VarintSubType.SInt64):
            value=self.decodeZigZag(value)
        elif self._subType==VarintSubType.Bool:
            value=bool(value)

        if self._fieldType==FieldType.Repeated:
            self._value.append(value)
        else: self._value=value

    def setValue(self, value):
        if self._value==value: return
        self._value=value

        if self._subType in (VarintSubType.SInt32, VarintSubType.SInt64):
            value=self.encodeZigZag(value, 32 if self._subType==VarintSubType.SInt32 else 64)

        data=getBytesForId(self._id,WireType.Varint)
        if self._subType in (VarintSubType.Int32, VarintSubType.UInt32, VarintSubType.SInt32):
            data.append((value&0x7F)|0x80)
            value=value>>7
            data.append(value&0x7F)

        elif self._subType in (VarintSubType.Int64, VarintSubType.UInt64, VarintSubType.SInt64, VarintSubType.Enum):
            for i in range(4):
                data.append((value&0x7F))
                value=value>>7
                if value==0: break

            for i in range(1,len(data)-1):
               data[i]|=0x80
        elif self._subType==VarintSubType.Bool:
            data.append(int(value))

        self._data=bytes(data)

    def __repr__(self):
        if self._subType!=VarintSubType.Enum:
           return super().__repr__()

        valueName=self._enum.reverse_mapping.get(self._value, None)
        return "{}({}: {})".format(self.__class__.__name__, self._id, valueName)

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

        if self._subType==LengthSubType.String:
            value=self._data.decode('utf8')
        elif self._subType== LengthSubType.Message:
            if not hasattr(self, "_mType"): raise Exception("_mType not set")           
            value = getMessageType(self._mType)()
            value.parse(self._data)            
        else: raise Error("Not implemented")
        
        
        if self._fieldType==FieldType.Repeated:
            self._value.append(value)
        else: self._value=value

    def setValue(self, value):
        if self._value==value: return
        self._value=value

        data=getBytesForId(self._id, self.type())
        data.append(len(value))
        self._data=bytes(data)
        if isinstance(value,bytes): self._data += value
        else:self._data+= bytes(value, "utf8")

FixedSubType=enum(
    Fixed64=1,
    SignedFixed64=2,
    Double=3,
    Fixed32=4,
    SignedFixed32=5,
    Float=6,
)

class Fixed(VarType):
    def __init__(self, id=None, data=None, subType=-1, fieldType=-1, **kwargs):
        super().__init__(id,data,subType,fieldType,**kwargs)
        if subType==FixedSubType.Float: self._fmt='<f'
        elif subType==FixedSubType.Double: self._fmt='<d'
        elif subType in (FixedSubType.Fixed32, FixedSubType.SignedFixed32): self._fmt="<i"
        elif subType in (FixedSubType.Fixed64, FixedSubType.SignedFixed64): self._fmt="<q"

    def type(self):
        if self._subType in (FixedSubType.Fixed64, FixedSubType.SignedFixed64, FixedSubType.Double):
            return WireType.Bit64
        else: return WireType.Bit32

    def setData(self, data):
        if self._data==data: return
        self._data=data

        value=self.decodeFixed(self._data, self._fmt)
        if self._fieldType==FieldType.Repeated:
            self._value.append(value)
        else: self._value=value

    def setValue(self, value):
        if self._value==value: return
        self._value=value
        
        data=bytes(getBytesForId(self._id,self.type()))
        self._data=data+self.encodeFixed(value,self._fmt)

    @staticmethod
    def encodeFixed(n, fmt='<f'): return struct.pack(fmt,n)

    @staticmethod
    def decodeFixed(n, fmt='<f'): return struct.unpack(fmt,n)[0]

@registerMessage
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
            self._fields[field['name']]=clazz(**field)

            name=field["name"]
            setattr(self.__class__, field['name'], property(partial(self.__get,name), partial(self.__set,name)))

        self.fields=self._fields

    @staticmethod
    def __get(name, instance):
        return instance._fields[name]

    @staticmethod
    def __set(name, instance, value):
        instance._fields[name].setValue(value)

    def __iter__(self):
       return iter(self._fields.keys())

    def reset(self):
        for field in self.values(): field.reset()

    def isValid(self):
        for field in self.values():
            if not field.isValid():
                print("Field {} is not valid!".format(field.id))
                return False
        else: return True

    def keys(self): return self._fields.keys()

    def values(self): return self._fields.values()

    def items(self): return self._fields.items()

    def serialize(self):
        data=b''
        for i in self._fieldsLUT.keys():
            name=self._fieldsLUT[i]
            d=self._fields[name].data()
            if d is not None: data+=d
        return data

    def parse(self, msg):
        self.reset()
        i=0
        while i<len(msg):
            byte=msg[i]           
            type=byte&0x7
            if not WireType.isValid(type):
                i+=1
                continue
            if byte <= 0x7f:#see https://github.com/nanopb/nanopb/blob/0f3dbba71d8d90b5ecfc1d01aed504c4ef642f80/pb_decode.c#L190
                id=byte>>3#fast path, single byte
            else:#varint
                bitpos = 0
                result =0
                while byte & 0x80:
                    result |= (byte&0x7F) << bitpos#result
                    bitpos += 7
                    i+=1
                    byte = msg[i]
                    if bitpos > 32:raise Exception("cant handle >32bit varint")
                result |= ((byte&0x7F) << bitpos)#result
                type=result&0x7
                id=result>>3

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
        return self.isValid()