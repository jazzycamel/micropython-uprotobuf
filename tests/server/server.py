from socketserver import TCPServer, BaseRequestHandler

from tests_pb2 import Test1 as Test1Message

class TestHandler(BaseRequestHandler):
    def handle(self):
        data=self.request.recv(1024).strip()
        print(b"Received:"+data)

        t1m=Test1Message()
        print("OK:",t1m.ParseFromString(data))

        print("Int32: ", t1m.Int32)
        print("Sint32: ", t1m.Sint32)
        print("Uint32: ", t1m.Uint32)

        print("Int64: ", t1m.Int64)
        print("Sint64: ", t1m.Sint64)
        print("Uint64: ", t1m.Uint64)

        print("Bool: ", t1m.Bool)

        print("Enum: ", t1m.Enum)

        print("Fixed32: ", t1m.Fixed32)
        print("Sfixed32: ", t1m.Sfixed32)

        print("Fixed64: ", t1m.Fixed64)
        print("Sfixed64: ", t1m.Sfixed64)

        print("Float: ", t1m.Float)
        print("Double: ", t1m.Double)

        print("String: ", t1m.String)

        self.request.sendall(data.upper())

if __name__=="__main__":
    HOST,PORT="localhost",6789
    with TCPServer((HOST,PORT), TestHandler) as server:
        server.serve_forever()