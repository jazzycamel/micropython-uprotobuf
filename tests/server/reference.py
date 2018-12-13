from tests_pb2 import Test1 as Test1Message

if __name__=="__main__":
    m=Test1Message()
    #m.Enum=Test1Message.ValueB
    m.Double=3.14
    print(m.SerializeToString())