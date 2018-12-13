# micropython-uprotobuf

## Project Status
This project is very much a work in progress and, as such, is incomplete. Currently protocol specifications can be compiled
via the plugin and messages can be parsed. 

### Things To Do
* Handle repeats and groups

## Usage
It is assumed that Google Protobuf has been installed and the compiler (`protoc`) is on the `$PATH`. It is also assumed that
a version of Python (preferably 3) is also available and the `protobuf` module has been installed (`pip install protobuf`).

Assuming you have a protocol specification file available (in this case called `test1.proto`) containing something like the following:

```proto
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

```sh
$ git clone https://github.com/jazzycamel/micropython-uprotobuf.git
$ cd micropython-uprotobuf
$ chmod +x uprotobuf_plugin.py
$ protoc test1.proto --plugin=protoc-gen-custom=uprotobuf_plugin.py --custom_out=. test1.proto
```

This will generate a python module named `test1_upb2.py`, which can be imported and used by micropython, containing a
class named `Test1Message`. This class can currently be used to parse binary messages as follows:

```python
from test1_upb2 import Test1Message

message=Test1Message()
ok=message.parse("\x08\x96\x01")
```

Note: this plugin was written for protobuf version 2. Version 3 has not been tested and may or may not work.

## Client/Server Example
In the `test` directory there are client and server scripts that demonstrate micropython encoding a message via
micropython-uprotobuf, transmitting that message via TCP and then decoding the message via the standard Google
protobuf python implementation.

First, run the server as follows:
```sh
$ cd tests/server
$ python3 server.py 
```

Then run the client as follows:
```sh
$ cd tests/client
$ micropython client.py
```

Both server and client use a protocol specification that can be found in `tests/proto/tests.proto`. There is also a 
script named `generate.sh` that is used to generate the python and micropython modules used by the example scripts.