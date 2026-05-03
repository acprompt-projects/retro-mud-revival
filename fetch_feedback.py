import requests, json

TOKEN = "acp_mcp_eyJzdWIiOiI5ZTAxZGI0Mi03ZDkzLTRhZjMtOTM1YS0yNmUyODdiMjU5NzgiLCJlbWFpbCI6ImRvcmVhbWVuZ0BnbWFpbC5jb20iLCJ0b2tlbl90eXBlIjoibWNwIiwianRpIjoiaEpaM2lTS2h3ZVV3RVdnX2N4RUQ1ZyIsImlhdCI6MTc3NzI4MTc1MTM4MiwiZXhwIjoxODA4ODE3NzUxMzgyfQ.zs30p_n1py2xjnkCC2ezoBsTc_6aTi2m4xmGeJHXcQE"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}
body = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "acp_check_inbox",
        "arguments": {"agent_id": "8908b95f-0c24-49dd-a8b4-bedf2c2af8c1", "limit": 5}
    },
    "id": 46
}

try:
    resp = requests.post("https://www.acprompt.com/api/mcp", headers=headers, json=body, timeout=15)
    data = resp.json()
    text = data["result"]["content"][0]["text"]
    inbox = json.loads(text)
    
    if inbox.get("messages"):
        msg = inbox["messages"][0]
        content = msg.get("content", {})
        body_text = content.get("body", "")
        with open("claude_feedback.txt", "w", encoding="utf-8") as f:
            f.write(f"From: {msg.get('from_agent_id')}\n")
            f.write(f"Type: {msg.get('message_type')}\n")
            f.write(f"Body:\n{body_text}\n")
        print("Feedback saved to claude_feedback.txt")
    else:
        print("No messages")
except Exception as e:
    print(f"Error: {e}")
