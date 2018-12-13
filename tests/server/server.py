from socketserver import TCPServer, BaseRequestHandler

class TestHandler(BaseRequestHandler):
    def handle(self):
        data=self.request.recv(1024).strip()
        print(b"Received:"+data)
        self.request.sendall(data.upper())

if __name__=="__main__":
    HOST,PORT="localhost",6789
    with TCPServer((HOST,PORT), TestHandler) as server:
        server.serve_forever()