#! python3
import json
import socket
import sys
import threading

import cc_info

assert __name__ == '__main__'


lprint_lock = threading.Lock()
def lprint(*a):
    with lprint_lock:
        print(*a)

g_lock = threading.Lock()
g_srcs = set()
g_includes = dict()

class SrcNode(object):
    pass


def process(parts):
    data = b''.join(parts)
    (cmd, data) = data.split(b'\0', 1)
    if cmd == b'echo':
        lprint(data.decode())
        return

    if cmd == b'add':
        data = data.split(b'\0')
        data = map(lambda x: x.decode(), data)

        with g_lock:
            cur = SrcNode()
            cur.name = next(data)
            lprint('[adding {}]'.format(cur.name))
            cur.preproc_time = int(next(data))
            cur.compile_time = int(next(data))
            cur.preproc_len = int(next(data))
            cur.includes = list()
            while True:
                try:
                    include = next(data)
                except StopIteration:
                    break

                cur.includes.append(include)
                g_includes.setdefault(include, set()).add(cur)
            g_srcs.add(cur)
        return

    lprint('unknown cmd: ' + cmd.decode())


class ExBadMagic(Exception):
    pass


def conn_thread(conn, addr):
    conn.settimeout(1.0)
    parts = [];
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
                parts.append(cur)

            process(parts)
        except (ExBadMagic, socket.error, socket.timeout):
            pass


def listen_thread(s):
    lprint('Listening on: ' + str(s.getsockname()))
    while True:
        (conn, addr) = s.accept()
        threading.Thread(target=conn_thread, args=(conn, addr), daemon=False).start()


for gai in socket.getaddrinfo('localhost', cc_info.PORT, proto=socket.IPPROTO_TCP):
    s = socket.socket(*gai[:3])
    s.bind(gai[4])
    s.listen()
    threading.Thread(target=listen_thread, args=(s,), daemon=True).start()

# --

def to_json(x):
    if hasattr(x, '__dict__'):
        return vars(x)
    if hasattr(x, '__iter__'):
        return list(x)
    assert False, dir(x)


while True:
    line = input()
    lprint('> ' + line)
    if not line:
        continue
    split = line.split(' ')
    cmd = split.pop(0)
    if cmd == 'dump':
        file_name = 'cc_info.json'
        with open(file_name, 'w', newline='\n') as f:
            with g_lock:
                includes = map(lambda x: (len(x[1]), x[0]), g_includes.items())
                includes = sorted(includes, key=lambda x: -x[0])
                x = {
                    'g_srcs': sorted(g_srcs, key=lambda x: -x.compile_time),
                    'g_includes': includes
                }
                json.dump(x, f, default=to_json, indent=3)
        lprint('Wrote: ' + file_name)
        continue

    lprint('???')



