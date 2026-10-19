"""Private electronics web dashboard."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from engine import IQOEngine

eng = IQOEngine(os.getenv("IQO_ARTIFACTS", "."), llm=os.getenv("IQO_LLM_MODE", "fallback"))

HTML = """<!doctype html><html><head><meta charset=utf-8><title>IQO Electronics AI</title>
<style>body{font:16px system-ui;background:#111827;color:#f3f4f6;max-width:900px;margin:35px auto;padding:0 20px}h1{color:#60a5fa}.card{background:#1f2937;border:1px solid #374151;border-radius:12px;padding:18px;margin:16px 0}textarea{width:100%;box-sizing:border-box;background:#111827;color:white;border:1px solid #4b5563;padding:12px;border-radius:8px}button{margin-top:10px;padding:10px 18px;background:#60a5fa;border:0;border-radius:7px;font-weight:bold}.safe{color:#86efac}.warn{color:#fbbf24}.critical{color:#f87171}.muted{color:#9ca3af;white-space:pre-wrap}</style></head>
<body><h1>IQO Electronics AI</h1><p class=muted>Trusted electronics and bench-safety brain. Chemistry and unrelated questions are refused.</p>
<div class=card><textarea id=q rows=4 placeholder="Ask about circuits, Ohm's law, batteries, measurements, or soldering..."></textarea><button onclick=ask()>Ask electronics brain</button></div><div id=out></div>
<script>async function ask(){let q=document.getElementById('q').value;let r=await fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});let d=await r.json();document.getElementById('out').innerHTML='<div class=card><h2 class="'+d.safety.toLowerCase()+'">'+d.safety+'</h2><p>'+d.tts+'</p><p class=muted>Topic: '+d.topic+' | Source: '+d.source+' | Latency: '+d.latency_ms.total+' ms</p></div>'} </script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data, content_type="application/json"):
        raw = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if urlparse(self.path).path == "/health": self.reply(200, {"status":"ok","domain":"electronics"})
        elif urlparse(self.path).path == "/": self.reply(200, HTML, "text/html; charset=utf-8")
        else: self.reply(404, {"error":"not found"})
    def do_POST(self):
        if urlparse(self.path).path != "/api/query": return self.reply(404, {"error":"not found"})
        try:
            body=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            question=str(body.get("question","")).strip()
            self.reply(200, eng.query(question))
        except (json.JSONDecodeError, ValueError) as e: self.reply(400, {"error":str(e)})
    def log_message(self, *_): pass

ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))), Handler).serve_forever()
