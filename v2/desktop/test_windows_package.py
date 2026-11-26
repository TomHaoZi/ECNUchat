"""Offline integration checks for the Windows release ZIP (Python standard library)."""
import http.client
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path

DESKTOP = Path(__file__).resolve().parent


@contextmanager
def temporary_release():
    temp = tempfile.TemporaryDirectory()
    try:
        yield Path(temp.name)
    finally:
        # Windows may retain a mapping on jvm.dll briefly after the EXE exits.
        for attempt in range(30):
            try:
                temp.cleanup()
                break
            except PermissionError:
                if attempt == 29:
                    raise
                time.sleep(.2)


@unittest.skipUnless(os.name == "nt", "Windows distribution")
@unittest.skipUnless(all(shutil.which(tool) for tool in ("javac", "jpackage", "node")),
                     "desktop integration requires a local JDK 21+ and Node.js")
class WindowsPackage(unittest.TestCase):
    def test_extracted_exe_serves_the_bundled_client_and_only_public_assets(self):
        version = subprocess.check_output(["javac", "-version"], text=True, stderr=subprocess.STDOUT)
        if int(version.split()[1].split(".")[0]) < 21:
            self.skipTest("desktop packaging requires JDK 21 or newer")
        with temporary_release() as temp:
            archive = temp / "release.zip"
            build = DESKTOP / "build_windows.py"
            self.assertTrue(build.is_file(), "the Windows release needs an offline build entry point")
            subprocess.run([sys.executable, build, "--output", archive], check=True)
            with zipfile.ZipFile(archive) as package:
                package.extractall(temp)
            release = temp / "ECNUchat-v2"
            self.assertTrue((release / "relay.py").is_file())
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            config = temp / "settings.json"
            config.write_text('{"relayUrl":"http://localhost:9182","other":"PRIVATE-CONFIG-FIELD"}', encoding="utf-8")
            env = dict(os.environ, ECNU_DESKTOP_CONFIG=str(config), ECNU_DESKTOP_PORT=str(port))
            env.pop("ECNU_RELAY_URL", None)
            proc = subprocess.Popen([release / "ECNUchat-v2.exe", "--serve-only"], env=env)

            def request(path, *, method="GET", headers=None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                try:
                    conn.request(method, path, headers=headers or {})
                    response = conn.getresponse()
                    return response.status, response.read()
                finally:
                    conn.close()

            try:
                deadline = time.monotonic() + 20
                while True:
                    try:
                        status, html = request("/")
                        break
                    except OSError:
                        if proc.poll() is not None or time.monotonic() >= deadline:
                            self.fail("the extracted native launcher did not serve its client")
                        time.sleep(.1)
                self.assertEqual(status, 200)
                self.assertLess(html.index(b"desktop-bridge.js"), html.index(b'src="app.js"'))
                for asset in (DESKTOP.parent / "pwa").rglob("*"):
                    if asset.is_file() and asset.name != "index.html":
                        route = "/" + asset.relative_to(DESKTOP.parent / "pwa").as_posix()
                        self.assertEqual(request(route), (200, asset.read_bytes()), route)
                status, bridge = request("/desktop-bridge.js")
                self.assertEqual(status, 200)
                self.assertNotIn(b"PRIVATE-CONFIG-FIELD", bridge)
                probe = "global.window={};" + bridge.decode() + "\nconsole.log(window.ECNUDesktop.resolveRelayUrl('http://localhost:9981'))"
                resolved = subprocess.check_output(["node", "-e", probe], text=True)
                self.assertEqual(resolved.strip(), "http://localhost:9182")
                self.assertEqual(request("/relay.py")[0], 404)
                self.assertEqual(request("/../desktop/config.js")[0], 404)
                self.assertEqual(request("/", method="POST")[0], 405)
                self.assertEqual(request("/", headers={"Host": "unrelated.invalid"})[0], 403)
            finally:
                proc.terminate()
                proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
