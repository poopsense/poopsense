"""Local-only reference adapter. Synthetic observations and fixed report, no AI inference."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse
from scripts.reader_device import unique_object, reject_constant, ClientError

ROOT = Path(__file__).resolve().parent
DEMO_KEY = "public-local-demo-key-not-a-secret-0001"
MAX_BYTES = 1024 * 1024
REPORT = """## 本次观察

这是一份预先编写的示例报告。页面上的形状和颜色来自合成请求，不用于判断健康状况。

## 下一次怎么观察

可切换示例中的形状和颜色，观察卡通展示；保存后可从历史列表重新打开同一条记录。

## 示例边界

此公开版本未调用大模型，也未执行传感分类、个人健康分析或设备动作。报告内容不会随样本变化。
"""


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("OBJECT_REQUIRED")
    template = json.loads((ROOT / "scripts/request-simulated.json").read_text(encoding="utf-8"))
    if set(payload) != set(template):
        raise ValueError("DEMO_FIELDS_MUST_MATCH_EXAMPLE")
    for field in ("device_id", "household_id", "session_id", "correlation_id"):
        if not isinstance(payload[field], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", payload[field]):
            raise ValueError("INVALID_IDENTIFIER")
    if payload["data_kind"] != "simulated" or payload["member_candidates"] != []:
        raise ValueError("SYNTHETIC_UNASSIGNED_DATA_ONLY")
    # This adapter accepts the documented fixture envelope, not the entire production schema.
    variable = {"device_id", "household_id", "session_id", "correlation_id", "observations"}
    if any(payload[k] != template[k] for k in template if k not in variable):
        raise ValueError("DEMO_ENVELOPE_MUST_MATCH_EXAMPLE")
    obs = payload["observations"]
    if not isinstance(obs, dict) or set(obs) != set(template["observations"]):
        raise ValueError("INVALID_OBSERVATIONS")
    for field, choices in {"shape": ("elongated", "compact", "scattered", "irregular"), "color": ("red", "green", "blue", "yellow")}.items():
        item = obs[field]
        if not isinstance(item, dict) or set(item) != set(template["observations"][field]):
            raise ValueError("INVALID_OBSERVATION_FIELDS")
        if item["value"] not in choices:
            raise ValueError("UNSUPPORTED_DEMO_LABEL")
        if any(item[k] != v for k, v in template["observations"][field].items() if k != "value"):
            raise ValueError("DEMO_METADATA_MUST_MATCH_EXAMPLE")
    if obs["odor"] != template["observations"]["odor"]:
        raise ValueError("ODOR_DISABLED_IN_DEMO")


@contextmanager
def connect(path):
    db = sqlite3.connect(path)
    try:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS sessions (device TEXT, session TEXT, payload TEXT, received TEXT, PRIMARY KEY(device,session))")
            yield db
    finally:
        db.close()


def record(row):
    payload = json.loads(row[2])
    return {"device_id": row[0], "session_id": row[1], "received_at": row[3],
            "correlation_id": payload["correlation_id"], "data_kind": "simulated",
            "assignment_status": "pending_claim", "assessment_status": "demo_only",
            "raw_observations": payload["observations"], "report_source": "fixed_fixture", "report": REPORT}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log payloads or request headers.

    def reply(self, status, body):
        encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def permitted(self):
        if self.headers.get("Host") not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
            self.reply(403, {"code": "LOOPBACK_HOST_REQUIRED"}); return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://127.0.0.1:5173", "http://localhost:5173", f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
            self.reply(403, {"code": "LOCAL_ORIGIN_REQUIRED"}); return False
        return True

    def do_GET(self):
        if not self.permitted(): return
        path = urlparse(self.path).path
        if path in ("/health", "/ready"):
            return self.reply(200, {"mode": "local_demo", "production_ready": False})
        if path == "/api/demo/example":
            return self.reply(200, json.loads((ROOT / "scripts/request-simulated.json").read_text(encoding="utf-8")))
        if path == "/api/demo/records":
            with connect(self.server.db_path) as db:
                rows = db.execute("SELECT * FROM sessions ORDER BY received DESC LIMIT 100").fetchall()
            return self.reply(200, [record(row) for row in rows])
        match = re.fullmatch(r"/api/v1/devices/([A-Za-z0-9_.-]+)/sessions/([A-Za-z0-9_.-]+)", path)
        if match:
            if self.headers.get("X-Device-Key") != DEMO_KEY:
                return self.reply(401, {"code": "DEMO_KEY_REQUIRED"})
            with connect(self.server.db_path) as db:
                row = db.execute("SELECT * FROM sessions WHERE device=? AND session=?", match.groups()).fetchone()
            if row:
                result = record(row)
                # Device response does not expose report text, matching the public subset boundary.
                result.pop("report"); result.pop("report_source")
                return self.reply(200, result)
        self.reply(404, {"code": "NOT_FOUND"})

    def do_POST(self):
        if not self.permitted(): return
        if self.path != "/api/v1/device-sessions":
            return self.reply(404, {"code": "NOT_FOUND"})
        if self.headers.get("X-Device-Key") != DEMO_KEY:
            return self.reply(401, {"code": "DEMO_KEY_REQUIRED"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if self.headers.get("Transfer-Encoding") or not 0 < size <= MAX_BYTES:
                return self.reply(413, {"code": "INVALID_BODY_SIZE"})
            self.connection.settimeout(10)
            body = self.rfile.read(size)
            payload = json.loads(body, object_pairs_hook=unique_object, parse_constant=reject_constant)
            canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
            validate(payload)
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, ClientError, TimeoutError):
            return self.reply(422, {"code": "INVALID_DEMO_PAYLOAD"})
        identity = (payload["device_id"], payload["session_id"])
        with connect(self.server.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM sessions WHERE device=? AND session=?", identity).fetchone()
            if row and row[2] != canonical:
                return self.reply(409, {"code": "IDEMPOTENCY_CONFLICT"})
            received = row[3] if row else datetime.now(timezone.utc).isoformat()
            if not row:
                db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (*identity, canonical, received))
        self.reply(202, {"session_id": identity[1], "device_id": identity[0], "duplicate": bool(row),
                         "data_kind": "simulated", "received_at": received, "assessment_status": "demo_only"})


def make_server(db_path, port=8000):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path): pass
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.db_path = path
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=str(ROOT / ".demo/sessions.sqlite3"))
    args = parser.parse_args()
    server = make_server(args.db, args.port)
    print(f"PoopSense local fixture API: http://127.0.0.1:{args.port}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
