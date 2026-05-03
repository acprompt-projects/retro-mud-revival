import socket, time, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 4000))
s.settimeout(3)

def recv_all():
    data = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            time.sleep(0.5)
    except socket.timeout:
        pass
    return data.decode('utf-8', errors='replace')

print('BANNER LEN:', len(recv_all()))

s.sendall(b'TestV4\r\n')
out = recv_all()
print('WELCOME LEN:', len(out))
if out:
    print('FIRST LINE:', out.split('\n')[0][:100])

cmds = ['status', 'quest', 'go north', 'talk laowang', 'quest accept kill_wolf', 'buy jian', 'save']
for c in cmds:
    s.sendall((c + '\r\n').encode('utf-8'))
    time.sleep(0.5)
    out = recv_all()
    first = out.split('\n')[0][:100] if out else '(empty)'
    print(f'CMD {c}: len={len(out)} first={first}')

s.close()
print('ALL DONE')
