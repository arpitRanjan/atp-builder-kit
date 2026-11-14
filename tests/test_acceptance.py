# scripts/acceptance.py: the checks, the ship bar, and the URL mode against a tiny local server.
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import acceptance  # noqa: E402


def test_cases_file_has_15_cases():
    cases = [json.loads(line) for line in open(ROOT / "evals" / "acceptance.jsonl")]
    assert len(cases) == 15 and len({c["id"] for c in cases}) == 15


def test_check_reasons():
    case = {"cite_any": ["qn-02"], "never_cite": ["qn-13"], "must_contain_any": ["Export"], "must_not_contain": ["refund"]}
    assert acceptance.check(case, {"text": "Choose Export.", "cited": ["qn-02"]}) == []
    reasons = acceptance.check(case, {"text": "We refund you.", "cited": ["qn-13"]})
    assert len(reasons) == 4


def test_local_run_meets_bar_and_misses_impossible_bar(capsys):
    assert acceptance.main(["--bar", "0.5"]) == 0
    assert "SHIP" in capsys.readouterr().out
    rows = acceptance.run([{"id": "x", "question": "zzzz qqqq", "cite_any": ["qn-01"]}], acceptance.ask_local)
    assert rows[0]["passed"] is False


def test_url_mode():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            reply = json.dumps({"text": "Open Export. " + body["question"], "cited": ["qn-02"]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/ask"
    try:
        # The fake server always cites qn-02, so only the PDF cases pass: well under a bar of 0.9.
        assert acceptance.main(["--bar", "0.9", "--url", url]) == 1
        assert acceptance.main(["--bar", "0.05", "--url", url]) == 0
    finally:
        server.shutdown()
