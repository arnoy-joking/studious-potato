from flask import Flask, request, Response
from flask_cors import CORS
import requests
import urllib.parse

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def proxy():
    if request.method == 'OPTIONS':
        return Response(status=200)

    # 1. Safely grab and decode the target URL from the query string
    raw_query = request.query_string.decode('utf-8')
    
    # If the URL is fully encoded (e.g., %3A%2F%2F), unquote it completely
    target_url = urllib.parse.unquote(raw_query)
    
    # Fallback strip: if the query string accidentally prepended a parameter name like "url="
    if target_url.startswith('url='):
        target_url = target_url.replace('url=', '', 1)

    if not target_url or not target_url.startswith('http'):
        print(f"❌ Invalid or missing target URL parsed: {target_url}")
        return {"error": f"Invalid target URL: {target_url}"}, 400

    print(f"🚀 Proxying {request.method} request to: {target_url}")

    # 2. Rebuild headers securely
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    try:
        # 3. Execute request to YouTube
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=True,
            timeout=10 # Prevent hanging forever
        )
        
        # Strip out hop-by-hop headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        resp_headers = [
            (name, value) for name, value in response.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        
        return Response(response.content, response.status_code, resp_headers)

    except Exception as e:
        # This will print the EXACT traceback in your terminal so we know exactly why it failed
        print(f"💥 Proxy Internal Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Proxy error: {str(e)}"}, 500

if __name__ == '__main__':
    print("Local CORS Proxy running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)