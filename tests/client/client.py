#!/usr/bin/env micropython
import sys
sys.path.append("../..")

from socket import socket, AF_INET, SOCK_STREAM

from tests_upb2 import Test1Message, Test1enum

if __name__=="__main__":
    HOST,PORT="localhost",6789
    s=socket(AF_INET,SOCK_STREAM)
    s.connect((HOST,PORT))

    t1m=Test1Message()

    # Varint types
    t1m.Int32=10
    t1m.Sint32=-10
    t1m.Uint32=15

    t1m.Int64=20
    t1m.Sint64=-20
    t1m.Uint64=25

    t1m.Bool=True

    t1m.Enum=Test1enum.ValueB

    # Fixed types
    t1m.Fixed32=30
    t1m.Sfixed32=-30

    t1m.Fixed64 = 40
    t1m.Sfixed64 = -40

    t1m.Float=3.14
    t1m.Double=-6.28

    # Length types
    t1m.String="My hovercraft is full of eels!"

    data=t1m.serialize()
    print("Sending: ",data)
    s.sendall(data)
    print(b"Received:"+s.recv(1024))