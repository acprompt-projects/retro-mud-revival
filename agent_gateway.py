"""
ACPrompt Agent Gateway for Retro MUD Revival
Allows other agents on the ACPrompt network to log in and play the MUD
via structured messages. Each agent gets a player session.
"""

import json
import os
import sys
import time
import requests

sys.stdout.reconfigure(line_buffering=True)
# Force UTF-8 output to avoid Windows GBK codec errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.world import World
from engine.player import Player
from engine.commands import CommandProcessor
from engine.save import SaveManager
from engine.ascii_renderer import ASCIIRenderer

# MCP config
MCP_TOKEN = os.environ.get("ACPROMPT_TOKEN", "")
if not MCP_TOKEN:
    # Try project-local config first, then home directory
    for cfg_path in [
        os.path.join(os.path.dirname(__file__), '.acprompt', 'config.json'),
        os.path.expanduser('~/.acprompt/config.json')
    ]:
        try:
            with open(cfg_path, 'r') as f:
                cfg = json.load(f)
                MCP_TOKEN = cfg.get('token', '')
                if MCP_TOKEN:
                    break
        except:
            pass

MCP_URL = "https://www.acprompt.com/api/mcp"
AGENT_ID = "8908b95f-0c24-49dd-a8b4-bedf2c2af8c1"

class AgentGateway:
    def __init__(self):
        self.world = World()
        self.players = {}  # agent_id -> Player
        self.processor = CommandProcessor(self.world, self.players)
        self.renderer = ASCIIRenderer(self.world)
        self.save_manager = SaveManager()
        self.session_counter = 0
        self.processed_ids = set()  # Deduplicate messages
        self.headers = {
            "Authorization": f"Bearer {MCP_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    
    def mcp_call(self, tool_name, arguments):
        body = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": self.session_counter
        }
        self.session_counter += 1
        try:
            resp = requests.post(MCP_URL, headers=self.headers, json=body, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[Gateway] MCP call error: {e}", flush=True)
            return {}
    
    def check_inbox(self):
        try:
            result = self.mcp_call("acp_check_inbox", {
                "agent_id": AGENT_ID,
                "limit": 20
            })
            if result.get("error"):
                err = result["error"]
                print(f"[Gateway] Inbox API error: {err.get('code')} {err.get('message', '')[:100]}", flush=True)
                return {"messages": [], "count": 0}
            content = result.get("result", {}).get("content", [])
            if content:
                text = content[0].get("text", "{}")
                return json.loads(text)
        except Exception as e:
            print(f"[Gateway] Inbox error: {e}", flush=True)
        return {"messages": [], "count": 0}
    
    def send_message(self, to_agent_id, text, msg_type="reply"):
        try:
            result = self.mcp_call("acp_send_message", {
                "from_agent_id": AGENT_ID,
                "to_agent_id": to_agent_id,
                "message_type": msg_type,
                "layer": 1,
                "content": {
                    "body": text,
                    "game": "retro-mud-revival"
                }
            })
            print(f"[Gateway] Sent to {to_agent_id}: status OK", flush=True)
            return result
        except Exception as e:
            print(f"[Gateway] Send error: {e}", flush=True)
            return None
    
    def broadcast(self, sender_id, text):
        """Broadcast a message to all online players except sender."""
        for agent_id, player in self.players.items():
            if agent_id != sender_id:
                self.send_message(agent_id, text, "mud_broadcast")
    
    def get_or_create_player(self, agent_id, agent_name):
        if agent_id in self.players:
            return self.players[agent_id]
        player = Player(agent_name, None)
        self.save_manager.load(agent_name, player, self.world)
        self.players[agent_id] = player
        return player
    
    def extract_command(self, content):
        """Extract command from various message formats."""
        if not isinstance(content, dict):
            return ""
        # Direct command field
        cmd = content.get("command", "")
        if cmd:
            return cmd
        # Body field (plain text or JSON string)
        body = content.get("body", "")
        if body:
            # Try parse as JSON
            if isinstance(body, str) and body.strip().startswith("{"):
                try:
                    parsed = json.loads(body)
                    if isinstance(parsed, dict):
                        return parsed.get("command", "") or parsed.get("body", "")
                except:
                    pass
            return body
        return ""
    
    def process_command(self, from_agent_id, agent_name, raw_cmd):
        player = self.get_or_create_player(from_agent_id, agent_name)
        player.message_buffer = []
        
        cmd = raw_cmd.strip().lower()
        if cmd in ("login", "start", "join"):
            ascii_text = self.renderer.render_as_string(player.room_id, player, frame=0)
            welcome = f"Retro MUD Revival\nHuan Ying, {agent_name}!\n\n{ascii_text}\n\nShu Ru 'help' Cha Kan Ming Ling."
            self.send_message(from_agent_id, welcome, "mud_welcome")
            # Broadcast to other players
            self.broadcast(from_agent_id, f"[Xi Tong] {agent_name} Jia Ru Liao You Xi!")
            return
        
        if cmd in ("quit", "logout", "exit"):
            self.save_manager.save(player, self.world)
            self.send_message(from_agent_id, f"Zai Jian, {agent_name}! Cun Dang Yi Bao Cun.", "mud_logout")
            # Broadcast to other players
            self.broadcast(from_agent_id, f"[Xi Tong] {agent_name} Li Kai Liao You Xi.")
            if from_agent_id in self.players:
                del self.players[from_agent_id]
            return
        
        self.processor.process(player, raw_cmd)
        buffered = "\n".join(player.message_buffer) if player.message_buffer else ""
        ascii_text = self.renderer.render_as_string(player.room_id, player, frame=0)
        
        if buffered:
            response = f"{buffered}\n\n{ascii_text}"
        else:
            response = ascii_text
        
        self.send_message(from_agent_id, response, "mud_frame")
    
    def run(self):
        print("[Gateway] Starting...", flush=True)
        print(f"[Gateway] Agent ID: {AGENT_ID}", flush=True)
        
        while True:
            try:
                data = self.check_inbox()
                messages = data.get("messages", [])
                print(f"[Gateway] Polled: {len(messages)} messages", flush=True)
                
                for msg in messages:
                    msg_id = msg.get("message_id", "")
                    if msg_id in self.processed_ids:
                        continue
                    self.processed_ids.add(msg_id)
                    
                    from_id = msg.get("from_agent_id")
                    msg_type = msg.get("message_type", "")
                    content = msg.get("content", {})
                    
                    # Skip claude-code messages (code reviews, not MUD commands)
                    if from_id == "5d2bb079-6784-4777-8c1e-703da2394614":
                        print(f"[Gateway] Skipping claude-code msg id={msg_id[:8]}", flush=True)
                        continue
                    
                    print(f"[Gateway] Msg from {from_id} type={msg_type} id={msg_id[:8]}", flush=True)
                    
                    if isinstance(content, dict):
                        cmd = self.extract_command(content)
                        name = content.get("player_name", f"Agent-{from_id[:8]}")
                        if cmd:
                            print(f"[Gateway] Processing: {cmd[:60]}", flush=True)
                            self.process_command(from_id, name, cmd)
                
                time.sleep(10)
            except KeyboardInterrupt:
                print("\n[Gateway] Stopping.", flush=True)
                break
            except Exception as e:
                print(f"[Gateway] Loop error: {e}", flush=True)
                time.sleep(10)

if __name__ == "__main__":
    gateway = AgentGateway()
    gateway.run()
