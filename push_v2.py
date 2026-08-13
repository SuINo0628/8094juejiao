import urllib.request
import json
import base64

url_base = 'http://127.0.0.1:11280/mcp'
token = '3YAiKl7OZ8rDB2pQb3RnvNCHtx6zLO1oNtUHKp3hqRE'

# Read HTML file
with open('C:/Users/Administrator/Desktop/8094juejiao/index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Read and base64 encode webp image
with open('C:/Users/Administrator/Desktop/8094juejiao/yueshenxing.webp', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('ascii')

print(f'HTML size: {len(html_content)} chars')
print(f'Image base64 size: {len(image_b64)} chars')

def send_mcp(data, session_id=None):
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
            return resp_body, sid, resp.status
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode('utf-8') if e.fp else str(e)
        return resp_body, None, e.code
    except Exception as e:
        return str(e), None, 0

def parse_sse(text):
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('data: '):
            try:
                return json.loads(line[6:])
            except:
                pass
    try:
        return json.loads(text)
    except:
        return text

def mcp_call(session_id, msg_id, tool_name, arguments):
    """Call a GitHub MCP tool"""
    msg = {
        'jsonrpc': '2.0', 'id': msg_id, 'method': 'tools/call',
        'params': {'name': tool_name, 'arguments': arguments}
    }
    resp, _, status = send_mcp(msg, session_id=session_id)
    parsed = parse_sse(resp)
    return parsed, status

# Step 1: Initialize
resp, sid, status = send_mcp({
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'py-client', 'version': '1.0.0'}
    }
})
print(f'Init: {status}, Session: {sid}')
session_id = sid

# Step 2: Notification
send_mcp({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, session_id=session_id)

# Step 3: Get user info
print('\n=== github_get_me ===')
parsed, status = mcp_call(session_id, 2, 'github_get_me', {})
if isinstance(parsed, dict) and 'result' in parsed:
    result = parsed['result']
    content = result.get('content', [{}])
    if content:
        print(f'User info: {content[0].get("text", "")[:300]}')
else:
    print(f'Response: {str(parsed)[:300]}')

# Step 4: Get current file info (to get SHA for update)
print('\n=== github_get_file_contents (index.html) ===')
parsed, status = mcp_call(session_id, 3, 'github_get_file_contents', {
    'owner': 'SuINo0628',
    'repo': '8094juejiao',
    'path': 'index.html',
    'branch': 'main'
})
html_sha = None
if isinstance(parsed, dict) and 'result' in parsed:
    result = parsed['result']
    content = result.get('content', [{}])
    if content:
        text = content[0].get('text', '')
        print(f'File info: {text[:400]}')
        # Try to extract SHA from the text
        try:
            file_data = json.loads(text)
            html_sha = file_data.get('sha')
            print(f'HTML SHA: {html_sha}')
        except:
            print(f'(could not parse SHA from text)')
else:
    print(f'Response: {str(parsed)[:400]}')

# Step 5: Try create_or_update_file for index.html
print('\n=== github_create_or_update_file (index.html) ===')
args = {
    'owner': 'SuINo0628',
    'repo': '8094juejiao',
    'path': 'index.html',
    'content': html_content,
    'message': 'Add yueshenxing (月神星) character with default breakup dialog',
    'branch': 'main'
}
if html_sha:
    args['sha'] = html_sha

parsed, status = mcp_call(session_id, 4, 'github_create_or_update_file', args)
if isinstance(parsed, dict) and 'result' in parsed:
    result = parsed['result']
    is_error = result.get('isError', False)
    content = result.get('content', [{}])
    text = content[0].get('text', '') if content else ''
    if is_error:
        print(f'ERROR: {text[:500]}')
    else:
        print(f'SUCCESS: {text[:500]}')
else:
    print(f'Response: {str(parsed)[:500]}')

# Step 6: Try create_or_update_file for yueshenxing.webp (new file)
print('\n=== github_create_or_update_file (yueshenxing.webp) ===')
parsed, status = mcp_call(session_id, 5, 'github_create_or_update_file', {
    'owner': 'SuINo0628',
    'repo': '8094juejiao',
    'path': 'yueshenxing.webp',
    'content': image_b64,
    'message': 'Add yueshenxing image asset',
    'branch': 'main'
})
if isinstance(parsed, dict) and 'result' in parsed:
    result = parsed['result']
    is_error = result.get('isError', False)
    content = result.get('content', [{}])
    text = content[0].get('text', '') if content else ''
    if is_error:
        print(f'ERROR: {text[:500]}')
    else:
        print(f'SUCCESS: {text[:500]}')
else:
    print(f'Response: {str(parsed)[:500]}')
