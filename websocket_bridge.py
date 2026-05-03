import asyncio
import socket
import websockets

TELNET_HOST = 'localhost'
TELNET_PORT = 4000
WS_HOST = '0.0.0.0'
WS_PORT = 8080

async def bridge(websocket):
    """Bridge a WebSocket client to the Telnet server."""
    peer = websocket.remote_address
    print(f"[WS] Client connected from {peer}")
    
    try:
        reader, writer = await asyncio.open_connection(TELNET_HOST, TELNET_PORT)
    except Exception as e:
        print(f"[WS] Failed to connect to Telnet: {e}")
        await websocket.close()
        return
    
    async def telnet_to_ws():
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                await websocket.send(data.decode('utf-8', errors='replace'))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[WS] Telnet→WS error: {e}")
    
    async def ws_to_telnet():
        try:
            async for message in websocket:
                writer.write(message.encode('utf-8'))
                await writer.drain()
        except websockets.exceptions.ConnectionClosed:
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[WS] WS→Telnet error: {e}")
    
    t2w = asyncio.create_task(telnet_to_ws())
    w2t = asyncio.create_task(ws_to_telnet())
    
    done, pending = await asyncio.wait(
        [t2w, w2t],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    for task in pending:
        task.cancel()
    
    writer.close()
    try:
        await writer.wait_closed()
    except:
        pass
    
    try:
        await websocket.close()
    except:
        pass
    
    print(f"[WS] Client disconnected {peer}")

async def main():
    print(f"[启动] WebSocket 桥接器: ws://{WS_HOST}:{WS_PORT}")
    print(f"[目标] Telnet 服务器: {TELNET_HOST}:{TELNET_PORT}")
    async with websockets.serve(bridge, WS_HOST, WS_PORT):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[关闭] 桥接器已停止")
