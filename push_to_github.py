import urllib.request
import json
import base64

url_base = 'http://127.0.0.1:11280/mcp'
token = '3YAiKl7OZ8rDB2pQb3RnvNCHtx6zLO1oNtUHKp3hqRE'

# Read files
with open('C:/Users/Administrator/Desktop/8094juejiao/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

with open('C:/Users/Administrator/Desktop/8094juejiao/yueshenxing.webp', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('ascii')

print(f'HTML size: {len(html_content)} chars')
print(f'Image base64 size: {len(image_b64)} chars')

def send_mcp(data, session_id=None):
    """Send MCP request and return (body, session_id, status)"""
    body = json.dumps(data).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': f'Bearer {token}',
    }
    if session_id:
        headers['Mcp-Session-Id'] = session_id

    req = urllib.request.Request(url_base, data=body, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            sid = resp.headers.get('Mcp-Session-Id')
            status = resp.status
            return resp_body, sid, status
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode('utf-8') if e.fp else str(e)
        return resp_body, None, e.code
    except Exception as e:
        return str(e), None, 0

def parse_sse(text):
    """Parse SSE response and extract JSON data"""
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('data: '):
            json_str = line[6:]
            try:
                return json.loads(json_str)
            except:
                pass
    try:
        return json.loads(text)
    except:
        return text

# Step 1: Initialize
print('=== Step 1: Initialize ===')
init_msg = {
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'py-client', 'version': '1.0.0'}
    }
}
resp, sid, status = send_mcp(init_msg)
print(f'Status: {status}, Session: {sid}')

session_id = sid
if not session_id:
    print('ERROR: No session ID!')
    exit(1)

# Step 2: Send initialized notification
print('\n=== Step 2: notifications/initialized ===')
notif = {'jsonrpc': '2.0', 'method': 'notifications/initialized'}
resp, _, status = send_mcp(notif, session_id=session_id)
print(f'Status: {status}, Response: {resp[:200]}')

# Step 3: Call push_files with both files
print('\n=== Step 3: push_files ===')
push_msg = {
    'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
    'params': {
        'name': 'github_push_files',
        'arguments': {
            'owner': 'SuINo0628',
            'repo': '8094juejiao',
            'branch': 'main',
            'message': 'Add yueshenxing (月神星) character with default breakup dialog + image asset',
            'files': [
                {'path': 'index.html', 'content': html_content},
                {'path': 'yueshenxing.webp', 'content': image_b64}
            ]
        }
    }
}
resp, _, status = send_mcp(push_msg, session_id=session_id)
print(f'Status: {status}')
parsed = parse_sse(resp)
if isinstance(parsed, dict):
    if 'result' in parsed:
        result_str = json.dumps(parsed['result'], ensure_ascii=False, indent=2)
        print(f'SUCCESS! Result: {result_str[:800]}')
    elif 'error' in parsed:
        error_str = json.dumps(parsed['error'], ensure_ascii=False, indent=2)
        print(f'ERROR: {error_str[:800]}')
    else:
        print(f'Response: {json.dumps(parsed, ensure_ascii=False)[:800]}')
else:
    print(f'Raw response: {str(parsed)[:800]}')
