import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.world import World
from engine.player import Player
from engine.commands import CommandProcessor

WORLD = World()
PLAYERS = {}
PROCESSOR = CommandProcessor(WORLD, PLAYERS)

BANNER = r"""
╔══════════════════════════════════════════╗
║        🏰 Retro MUD Revival 🏰           ║
║     复刻早期经典文字 MUD 游戏             ║
╠══════════════════════════════════════════╣
║  命令: look, go, take, attack, talk...   ║
║  输入 help 查看完整命令列表               ║
╚══════════════════════════════════════════╝
"""

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"[连接] {addr}")
    
    writer.write(BANNER.encode('utf-8'))
    writer.write("\n请输入你的冒险者姓名: ".encode('utf-8'))
    await writer.drain()
    
    name_data = await reader.readline()
    if not name_data:
        writer.close()
        return
    
    name = name_data.decode('utf-8', errors='ignore').strip()
    if not name:
        name = "无名冒险者"
    
    player = Player(name, writer)
    
    # Try load save
    from engine.save import SaveManager
    sm = SaveManager()
    loaded = sm.load(name, player, WORLD)
    
    PLAYERS[name] = player
    
    if loaded:
        writer.write(f"\n欢迎回来，{name}！存档已读取。\n".encode('utf-8'))
    else:
        writer.write(f"\n欢迎，{name}！你来到了一个宁静的小村庄...\n".encode('utf-8'))
    await writer.drain()
    
    # Initial look
    PROCESSOR.cmd_look(player, [], "")
    await writer.drain()
    
    writer.write(b"\n> ")
    await writer.drain()
    
    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            
            raw = data.decode('utf-8', errors='ignore').strip()
            if raw.lower() == 'quit':
                PROCESSOR.cmd_quit(player, [], "")
                break
            
            PROCESSOR.process(player, raw)
            
            if player.writer and not player.writer.is_closing():
                writer.write(b"\n> ")
                await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        print(f"[错误] {name}: {e}")
    finally:
        print(f"[断开] {name} ({addr})")
        if name in PLAYERS:
            del PLAYERS[name]
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

async def main():
    host = '0.0.0.0'
    port = 4000
    server = await asyncio.start_server(handle_client, host, port)
    print(f"[启动] Retro MUD Revival 服务器运行在 {host}:{port}")
    print(f"[提示] 用 telnet localhost 4000 或 Putty/Windows Telnet 连接")
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[关闭] 服务器已停止")
