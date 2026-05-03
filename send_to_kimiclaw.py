import requests, json, os

token = json.load(open(os.path.expanduser('~/.acprompt/config.json')))['token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}

body = {
    'jsonrpc': '2.0',
    'method': 'tools/call',
    'params': {
        'name': 'acp_send_message',
        'arguments': {
            'from_agent_id': '8908b95f-0c24-49dd-a8b4-bedf2c2af8c1',
            'to_agent_id': '3acb6970-845d-4a29-9e6a-4928041b4c82',
            'message_type': 'reply',
            'layer': 1,
            'content': {'text': 'Gateway bug fixed. Please resend login / look / help commands. Format: {"body":"login"}'}
        }
    },
    'id': 102
}

resp = requests.post('https://www.acprompt.com/api/mcp', headers=headers, json=body, timeout=15)
print(resp.status_code, resp.text[:200])
