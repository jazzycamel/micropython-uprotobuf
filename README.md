# micropython-uprotobuf

## Project Status
This project is very much a work in progress and as such is incomplete. Currently protocol specifications can be compiled
via the plugin and messages can be parsed. 

### Things To Do
* Implement Serialisation (most of the nuts and bolts are there)


## Usage
It is assumed that Google Protobuf has been installed and the compiler (`protoc`) is on the `$PATH`. It is also assumed that
a version of Python (preferably 3) is also available and the `protobuf` module has been installed (`pip install protobuf`).

Assuming you have a protocol specification file available (in this case called `test1.proto`) containing something like the following:

```
syntax = "proto2";

package test1;

message test1 {
  enum test1enum {
    ValueA=1;
    ValueB=2;
    ValueC=3;
  }

  required int32 a = 1;
  required string b = 2;
  required int64 c = 4;
  required float d = 5;
  required double e = 6;
  required test1enum f = 7 [default=ValueA];
  optional bool g = 8;
  repeated fixed32 h = 9;
  required sint32 i = 10;
  required sfixed64 j = 11;
}
```

then a micropython compatible module can be created using the uprotobuf plugin as follows: 

```
$ git clone https://github.com/jazzycamel/micropython-uprotobuf.git
$ cd micropython-uprotobuf
$ chmod +x uprotobuf_plugin.py
$ protoc test1.proto --plugin=protoc-gen-custom=uprotobuf_plugin.py --custom_out=. test1.proto
```

This will generate a python module named `test1_upb2.py`, which can be imported and used by micropython, containing a
class named `Test1Message`. This class can currently be used to parse binary messages as follows:

```
from test1_upb2 import Test1Message

message=Test1Message()
ok=message.parse("\x08\x96\x01")
```

Note: this plugin was written for protobuf version 2. Version 3 has not been tested and may or may not work.
