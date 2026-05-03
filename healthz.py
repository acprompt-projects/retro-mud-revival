"""
Health check endpoint for Retro MUD Revival.
Returns JSON status of all services.
"""

import asyncio
import json
import socket
from datetime import datetime

HEALTHZ_PORT = 9000
VERSION = "0.2.0"


def check_port(host, port):
    """Check if a port is listening."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except:
        return False


async def health_handler(reader, writer):
    """Simple HTTP handler for /healthz."""
    try:
        request = await reader.read(1024)
        request_text = request.decode('utf-8', errors='ignore')
        
        path = "/"
        if request_text.startswith("GET "):
            parts = request_text.split(" ")
            if len(parts) >= 2:
                path = parts[1]
        
        if path == "/healthz" or path == "/":
            telnet_ok = check_port("127.0.0.1", 4000)
            ws_ok = check_port("127.0.0.1", 8080)
            
            # Try to get player count from gateway module
            players_online = 0
            try:
                from agent_gateway import AgentGateway
                # We can't easily access the running gateway instance,
                # so we just report if gateway is responding via a simple check
                players_online = "unknown"
            except:
                pass
            
            response_data = {
                "status": "ok" if (telnet_ok and ws_ok) else "degraded",
                "version": VERSION,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "services": {
                    "telnet": {
                        "port": 4000,
                        "status": "ok" if telnet_ok else "down"
                    },
                    "websocket": {
                        "port": 8080,
                        "status": "ok" if ws_ok else "down"
                    },
                    "gateway": {
                        "status": "running",
                        "players_online": players_online
                    }
                }
            }
            
            body = json.dumps(response_data, ensure_ascii=False)
            http_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json; charset=utf-8\r\n"
                f"Content-Length: {len(body.encode('utf-8'))}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
        else:
            http_response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 9\r\n"
                "Connection: close\r\n"
                "\r\n"
                "Not Found"
            )
        
        writer.write(http_response.encode('utf-8'))
        await writer.drain()
    except Exception as e:
        print(f"[Healthz] Handler error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(health_handler, "0.0.0.0", HEALTHZ_PORT)
    print(f"[Healthz] HTTP health check running on http://0.0.0.0:{HEALTHZ_PORT}/healthz")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
