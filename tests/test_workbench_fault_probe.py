import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def probe():
    spec = importlib.util.spec_from_file_location("awb_fault_probe", ROOT / "tools/workbench_fault_probe.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def target(directory, copy_expected):
    directory.mkdir()
    source = '''import argparse,json,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,HTTPServer
p=argparse.ArgumentParser(); p.add_argument('--data'); p.add_argument('--port',type=int); p.add_argument('--profile'); a=p.parse_args()
profile=json.load(open(a.profile)); tasks={}
class H(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def send(self,status,value):
  b=json.dumps(value).encode(); self.send_response(status); self.end_headers(); self.wfile.write(b)
 def do_GET(self):
  if self.path=='/': self.send(200,'<button>Tasks</button>')
  else: self.send(200,list(tasks.values()))
 def do_POST(self):
  b=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  if self.path=='/api/tasks': tasks['one']=b|{'id':'one'}; self.send(200,tasks['one']); return
  if self.path.endswith('/approve'): self.send(200,{}); return
  try:
   data=json.dumps({'prompt':'execute','cwd':__import__('os').getcwd()}).encode()
   req=urllib.request.Request(profile['gateway']+'/noninteractive',data=data,headers={'Content-Type':'application/json'})
   result=json.loads(json.load(urllib.request.urlopen(req,timeout=2))['text'])
   output=tasks['one']['expected'] if COPY_EXPECTED else result
   self.send(200,{'output':output,'verified':output==tasks['one']['expected']})
  except urllib.error.HTTPError: self.send(503,{'error':'backend failed','verified':False})
HTTPServer(('127.0.0.1',a.port),H).serve_forever()
'''.replace("COPY_EXPECTED", repr(copy_expected))
    (directory / "app.py").write_text(source, encoding="utf-8")
    return directory


def test_fault_probe_rejects_expected_copy_even_when_node_was_called(tmp_path):
    result = probe().run(target(tmp_path / "bad", True), {"title": "sum", "input": {"values": [2, 3]},
        "expected": {"sum": 5}}, tmp_path / "bad-probe")
    assert not result["passed"]
    assert result["checks"]["wrong_result_rejected"] is False
    assert result["actual_model_calls"] == 0 and not result["release_qualified"]


def test_fault_probe_checks_actual_rejection_and_keeps_sources_unchanged(tmp_path):
    workspace = target(tmp_path / "good", False)
    (workspace / "app.py").write_text((workspace / "app.py").read_text().replace("self.send(200,tasks['one'])", "self.send(201,tasks['one'])"), encoding="utf-8")
    before = (workspace / "app.py").read_bytes()
    result = probe().run(workspace, {"title": "sum", "input": {"values": [2, 3]},
        "expected": {"sum": 5}}, tmp_path / "good-probe")
    assert result["passed"] and result["checks"]["wrong_result_rejected"]
    assert result["checks"]["backend_failure_explicit"]
    assert (workspace / "app.py").read_bytes() == before
    assert not result["construction_retry"] and result["simulated_node"]
