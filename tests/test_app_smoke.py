from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib import request


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AppSmokeTests(unittest.TestCase):
    def test_server_doctor_generate_and_export(self) -> None:
        base = os.getenv("STORYSEED_TEST_TMP") or tempfile.gettempdir()
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            env = os.environ.copy()
            env["STORYSEED_HOME"] = tmp
            env["STORYSEED_DISABLE_OPEN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, "-m", "storyseed_app.app", "--no-open", "--port", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            try:
                url = self._read_url(proc)
                doctor = self._json(url + "/api/doctor")
                self.assertTrue(doctor["ok"])
                self.assertTrue(doctor["doctor"]["state_ok"])

                for asset in self._manifest_assets():
                    with request.urlopen(url + f"/static/assets/{asset['file']}", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.headers.get_content_type(), asset["content_type"])
                        self.assertGreater(len(response.read()), 100_000)

                safety = self._json(url + "/api/safety")
                self.assertTrue(safety["ok"])
                self.assertEqual(safety["safety"]["status"], "green")

                started = time.perf_counter()
                generated = self._post_json(
                    url + "/api/generate",
                    {"seed": 5150, "mode": "Story Starter", "age_band": "8-11", "creativity": 55},
                )
                self.assertLess(time.perf_counter() - started, 2)
                self.assertTrue(generated["ok"])
                prompt = generated["prompt"]
                self.assertIn("Student Task:", prompt["prompt"])

                exported = self._post_json(url + "/api/export", {"prompt": prompt, "format": "txt"})
                self.assertTrue(exported["ok"])
                self.assertTrue(exported["export"]["path"].startswith(tmp))

                html_exported = self._post_json(url + "/api/export", {"prompt": prompt, "format": "html"})
                self.assertTrue(html_exported["ok"])
                self.assertTrue(html_exported["export"]["path"].startswith(tmp))

                open_export = self._post_json(url + "/api/open-export", {"path": html_exported["export"]["path"]})
                self.assertTrue(open_export["ok"])
                self.assertFalse(open_export["export_file"]["opened"])

                open_exports = self._post_json(url + "/api/open-exports", {})
                self.assertTrue(open_exports["ok"])
                self.assertFalse(open_exports["export_folder"]["opened"])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()

    def _read_url(self, proc: subprocess.Popen[str]) -> str:
        assert proc.stdout is not None
        deadline = time.time() + 8
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                return match.group(0)
        self.fail("Server did not print a local URL")

    def _json(self, url: str) -> dict:
        with request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _manifest_assets(self) -> list[str]:
        manifest_path = PROJECT_ROOT / "storyseed_app" / "static" / "assets" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return manifest["assets"]


if __name__ == "__main__":
    unittest.main()
