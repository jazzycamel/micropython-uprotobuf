from test1_upb2 import Test1Message

if __name__=="__main__":
    m=Test1Message()

    print("Simple\n======")
    msg=b"\x08\x96\x01"
    ok=m.parse(msg)
    for k,v in m.items(): print(k,v)
    print("OK" if ok else "Failed!")
    print()
    #
    # print("String\n======")
    # msg=b'\x08\x96\x01\x12\x07testing'
    # ok=m.parse(msg)
    # for k,v in m.items(): print(k,v)
    # print("OK" if ok else "Failed!")
    # print()
    #
    # print("Complex\n=======")
    # msg=b'\x08\x96\x01\x12\x07testing \x80\x80\x80\x80\x10-\x00\x00\x80?1\x00\x00\x00\x00\x00\x00\x00@8\x01@\x01M\x11\x00\x00\x00M\x12\x00\x00\x00PSY\xb7\xff\xff\xff\xff\xff\xff\xff'
    # ok=m.parse(msg)
    # for k,v in m.items(): print(k,v)
    # print("OK" if ok else "Failed!")
    # print()
    #
    # m.a=120
    # print(m.a)

    print(m.parse(b'\x08\n'))
    print(m.a)
    print(m.a.value())