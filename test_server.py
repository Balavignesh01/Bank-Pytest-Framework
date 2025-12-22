from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from urllib.parse import urlparse
from run_tests import run_pytest

HOST = "127.0.0.1"
PORT = 5001
class TestServer(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    def do_OPTIONS(self):
        self._set_headers(200)
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/run-tests":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw_body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        action = payload.get("action")
        os.environ["UI_ACTION"] = action or ""
        ui_accounts = payload.get("accounts", [])
        ui_session = payload.get("session")
        ui_transfers = payload.get("transfers", [])
        os.environ["UI_ACCOUNTS"] = json.dumps(ui_accounts)
        os.environ["UI_SESSION"] = json.dumps(ui_session)
        os.environ["UI_TRANSFERS"] = json.dumps(ui_transfers)
        print("\n-------------------------------------------")
        print(f"[test_server] Received test trigger from UI: {action}")
        print(f"[test_server] UI accounts received: {len(ui_accounts)}")
        print("[test_server] Running pytest...")
        print("-------------------------------------------")
        result = run_pytest(action)
        print("\n[test_server] Completed tests for:", action)
        print("[test_server] Success:", result.get("success"))
        print("-------------------------------------------\n")

        self._set_headers(200)
        self.wfile.write(json.dumps(result).encode("utf-8"))
def main():
    print(f"[test_server] Listening on http://{HOST}:{PORT}")
    print("[test_server] Waiting for actions from React UI...")
    server = HTTPServer((HOST, PORT), TestServer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[test_server] Shutting down...")
    finally:
        server.server_close()
if __name__ == "__main__":
    main()