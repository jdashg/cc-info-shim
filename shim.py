#! python3
import socket
import subprocess
import sys
import time

import cc_info

assert __name__ == '__main__'

SHOW_INCLUDES = '-H'
SHOW_INCLUDES = '-showIncludes'



class ExShimOut(Exception):
    pass

def send(cmd, payload):
    conn = socket.create_connection(('localhost', cc_info.PORT), 0.300)
    conn.sendall(cc_info.MAGIC)
    conn.sendall(cmd)

    for x in payload:
        conn.sendall(b'\0')
        conn.sendall(x.encode())


cc_args = sys.argv[1:]
shim_out = False
try:
    if '-c' not in cc_args:
        raise ExShimOut('no -c')

    srcName = cc_args[-1]
    ext = srcName.rsplit('.')[-1]
    if ext not in ('cpp', 'cc', 'c'):
        raise ExShimOut('bad src ext')

    info_args = cc_args[:-1] + ['-E', SHOW_INCLUDES, cc_args[-1]]
    start = time.time()
    p = subprocess.run(info_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise ExShimOut('info_args failed to run')
    preproc_time = time.time() - start

    (preproc, includes) = (p.stdout, p.stderr)
except ExShimOut as e:
    send(b'echo', ['[ExShimOut: {}]'.format(e.args[0])])
    shim_out = True
    pass

start = time.time()
shimmed = subprocess.run(cc_args)
compile_time = time.time() - start

if shim_out or shimmed.returncode != 0:
    exit(shimmed.returncode)

# --

payload = [
    srcName,
    str(int(preproc_time*1000)),
    str(int(compile_time*1000)),
    str(len(preproc))
]

prefix = b'Note: including file: '
for x in includes.split(b'\r\n'):
    if not x.startswith(prefix):
        continue
    x = x[len(prefix):]
    payload.append(x.decode())

# --

send(b'add', payload)
exit(0)
