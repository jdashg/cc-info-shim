#! python3
import socket
import sys
import threading

import cc_info

assert __name__ == '__main__'


lprint_lock = threading.Lock()
def lprint(*a):
    with lprint_lock:
        print(*a)


def process(data):
    data = data.split(b'\0')
    data = map(lambda x: x.decode(), data)
    data = list(data)
    lprint(data[0])


class ExBadMagic(Exception):
    pass


def conn_thread(conn, addr):
    conn.settimeout(1.0)
    data = [];
    with conn:
        try:
            magic = conn.recv(len(cc_info.MAGIC))
            if magic != cc_info.MAGIC:
                lprint('[bad magic from {}]'.format(addr))
                raise ExBadMagic()

            while True:
                cur = conn.recv(4096)
                if not cur:
                    break
                data.append(cur)
        except (ExBadMagic, socket.error, socket.timeout):
            pass

    data = b''.join(data)
    process(data)


def listen_thread(s):
    lprint('Listening on {}.'.format(s.getsockname()))
    while True:
        (conn, addr) = s.accept()
        threading.Thread(target=conn_thread, args=(conn, addr), daemon=False).start()


for gai in socket.getaddrinfo('localhost', cc_info.PORT, proto=socket.IPPROTO_TCP):
    s = socket.socket(*gai[:3])
    s.bind(gai[4])
    s.listen()
    threading.Thread(target=listen_thread, args=(s,), daemon=True).start()


while True:
    line = input()
    lprint('> ' + line)
