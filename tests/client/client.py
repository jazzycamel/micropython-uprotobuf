#!/usr/bin/env micropython
import sys
sys.path.append("../..")

from socket import socket, AF_INET, SOCK_STREAM

from tests_upb2 import Test1Message, Test1enum

if __name__=="__main__":
    #HOST,PORT="localhost",6789
    #s=socket(AF_INET,SOCK_STREAM)
    #s.connect((HOST,PORT))

    t1m=Test1Message()
    #t1m.Enum=Test1enum.ValueB
    t1m.String="My hovercraft is full of eels!"

    print(t1m.serialize())

    #s.sendall(t1m.serialize())
    #print(b"Received:"+s.recv(1024))