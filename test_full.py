import socket, time

def run_test():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 4000))
    s.settimeout(2)
    
    def recv():
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                time.sleep(0.3)
        except socket.timeout:
            pass
        return data.decode('utf-8', errors='replace')
    
    recv()  # banner
    s.sendall(b'TestPlayer\r\n')
    recv()  # welcome + look
    
    cmds = ['status', 'quest', 'go north', 'talk laowang', 'quest accept kill_wolf', 'buy jian', 'save', 'go south', 'go south', 'attack wolf']
    results = []
    for c in cmds:
        s.sendall((c + '\r\n').encode('utf-8'))
        time.sleep(0.4)
        out = recv()
        results.append(f"=== {c} ===\n{out}\n")
    
    s.close()
    
    with open('test_full_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))
    print('Test complete. See test_full_output.txt')

if __name__ == '__main__':
    run_test()
