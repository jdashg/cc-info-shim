#! python3
import socket
import sys

import cc_info

assert __name__ == '__main__'


def report(data):
    data = map(lambda x: x.encode(), data)
    data = b'\0'.join(data)

    conn = socket.create_connection(('localhost', cc_info.PORT), 1.0)
    conn.sendall(cc_info.MAGIC)
    conn.sendall(data)
    conn.close()


print(sys.argv)
cc_args = sys.argv[1:]
report(cc_args)
