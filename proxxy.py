from flask import Flask, request, Response
from flask_cors import CORS
import requests
import urllib.parse

app = Flask(__name__)
# Securely enable CORS for your local development
CORS(app)

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
def proxy():
    if request.method == 'OPTIONS':
        return Response(status=200)

    # 1. Safely grab and decode the target URL from the query string
    raw_query = request.query_string.decode('utf-8')
    target_url = urllib.parse.unquote(raw_query)
    
    if target_url.startswith('url='):
        target_url = target_url.replace('url=', '', 1)

    if not target_url or not target_url.startswith('http'):
        return {"error": f"Invalid target URL: {target_url}"}, 400

    print(f"🚀 Proxying {request.method} to: {target_url}")

    # 2. Rebuild headers
    # We EXCLUDE 'Accept-Encoding' so YouTube returns plain text/JSON instead of Gzip
    # We EXCLUDE 'Host' because it must match the destination server
    excluded_request_headers = ['host', 'accept-encoding']
    headers = {
        key: value for key, value in request.headers 
        if key.lower() not in excluded_request_headers
    }
    
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    try:
        # 3. Execute request
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=True,
            timeout=15
        )
        
        # 4. Filter response headers
        # Remove hop-by-hop headers and compression headers
        # Since 'requests' decompresses automatically, the content-length will change,
        # so we let Flask recalculate it.
        excluded_resp_headers = [
            'content-encoding', 
            'content-length', 
            'transfer-encoding', 
            'connection', 
            'server'
        ]
        
        resp_headers = [
            (name, value) for name, value in response.raw.headers.items()
            if name.lower() not in excluded_resp_headers
        ]
        
        # response.text contains the decompressed string content
        return Response(response.content, response.status_code, resp_headers)

    except Exception as e:
        print(f"💥 Proxy Internal Error: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print("Local CORS Proxy running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)