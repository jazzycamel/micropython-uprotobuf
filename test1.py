from test1_upb2 import Test1Message

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
