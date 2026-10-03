import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from demo_server import make_server, DEMO_KEY
from scripts import reader_device


class DemoIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "records.sqlite3"
        self.server = make_server(self.path, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.sample = json.loads((Path(__file__).parent / "scripts/request-simulated.json").read_text())

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.temp.cleanup()

    def call(self, path, body=None, key=DEMO_KEY, origin=None):
        headers = {"X-Device-Key": key, "Content-Type": "application/json"}
        if origin: headers["Origin"] = origin
        req = urllib.request.Request(self.base + path, data=body, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def upload(self, payload):
        return self.call("/api/v1/device-sessions", json.dumps(payload).encode())

    def test_persistence_and_idempotency(self):
        self.assertEqual(self.upload(self.sample)[0], 202)
        self.assertTrue(self.upload(self.sample)[1]["duplicate"])
        changed = copy.deepcopy(self.sample); changed["observations"]["color"]["value"] = "blue"
        self.assertEqual(self.upload(changed)[0], 409)
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.server = make_server(self.path, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        records = self.call("/api/demo/records")[1]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["raw_observations"]["color"]["value"], "red")
        self.assertEqual(records[0]["report_source"], "fixed_fixture")

    def test_actual_upload_client_interoperates(self):
        previous = reader_device.BASE_URL
        reader_device.BASE_URL = self.base
        try:
            result = reader_device.request_once(self.sample, DEMO_KEY, json.dumps(self.sample).encode())
            self.assertFalse(result["result"]["duplicate"])
            result = reader_device.request_once(self.sample, DEMO_KEY)
            self.assertEqual(result["result"]["device_id"], "demo_device")
            self.assertNotIn("report", result["result"])
        finally: reader_device.BASE_URL = previous

    def test_reject_real_data_and_credentials(self):
        for field, value in [("data_kind", "hardware_test"), ("member_candidates", [{"member_ref":"person"}]), ("secret", "should-not-be-stored")]:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.sample); payload[field] = value
                self.assertEqual(self.upload(payload)[0], 422)
        self.assertEqual(self.call("/api/demo/records")[1], [])

    def test_invalid_json_auth_and_origin(self):
        route = "/api/v1/device-sessions"
        for body in [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e1000}', b'[]']:
            self.assertEqual(self.call(route, body)[0], 422)
        self.assertEqual(self.call(route, json.dumps(self.sample).encode(), key="wrong")[0], 401)
        self.assertEqual(self.call(route, json.dumps(self.sample).encode(), origin="https://example.com")[0], 403)
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        try:
            conn.putrequest("POST", route)
            conn.putheader("X-Device-Key", DEMO_KEY)
            conn.putheader("Content-Length", str(1024 * 1024 + 1))
            conn.endheaders()
            self.assertEqual(conn.getresponse().status, 413)
        finally: conn.close()


if __name__ == "__main__": unittest.main()
