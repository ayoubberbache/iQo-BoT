"""Private chemistry web dashboard."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from engine import IQOEngine

eng = IQOEngine(os.getenv("IQO_ARTIFACTS", "."), llm=os.getenv("IQO_LLM_MODE", "fallback"))

HTML = """<!doctype html><html><head><meta charset=utf-8><title>IQO Chemistry AI</title>
<style>body{font:16px system-ui;background:#101820;color:#eef2f3;max-width:900px;margin:35px auto;padding:0 20px}h1{color:#55d6be}.card{background:#172630;border:1px solid #2f4652;border-radius:12px;padding:18px;margin:16px 0}textarea{width:100%;box-sizing:border-box;background:#0c1419;color:white;border:1px solid #456;padding:12px;border-radius:8px}button{margin-top:10px;padding:10px 18px;background:#55d6be;border:0;border-radius:7px;font-weight:bold}.safe{color:#55d6be}.warn{color:#ffc857}.critical{color:#ff6b6b}.muted{color:#9fb0b8;white-space:pre-wrap}</style></head>
<body><h1>IQO Chemistry AI</h1><p class=muted>Trusted chemistry and laboratory-safety brain. Unrelated questions are refused.</p>
<div class=card><textarea id=q rows=4 placeholder="Ask about titration, pH, reagents, equations, or lab safety..."></textarea><button onclick=ask()>Ask chemistry brain</button></div><div id=out></div>
<script>async function ask(){let q=document.getElementById('q').value;let r=await fetch('/api/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});let d=await r.json();document.getElementById('out').innerHTML='<div class=card><h2 class="'+d.safety.toLowerCase()+'">'+d.safety+'</h2><p>'+d.tts+'</p><p class=muted>Topic: '+d.topic+' | Source: '+d.source+' | Latency: '+d.latency_ms.total+' ms</p></div>'} </script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data, content_type="application/json"):
        raw = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        self.send_response(code); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if urlparse(self.path).path == "/health": self.reply(200, {"status":"ok","domain":"chemistry"})
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
