"""Run with the repository environment: python -m pytest -s v2/tests/test_voice_browser.py.

Uses a local Chrome/Chromium/Edge installation (override with ECNUCHAT_CHROMIUM).
The browser and relay are disposable. Chromium supplies the microphone samples.
"""

import ipaddress
import json
import os
import shutil
import subprocess
import threading
import time
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import create_connection
from tempfile import TemporaryDirectory

import pytest
from websockets.sync.client import connect

from v2.relay.relay import Handler, MemoryStore, Relay


PWA = Path(__file__).resolve().parents[1] / "pwa"
LOOPBACK = "127.0.0.1"


class Assets(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve(handler):
    with ThreadingHTTPServer((LOOPBACK, 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://{LOOPBACK}:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


def find_browser():
    if path := os.environ.get("ECNUCHAT_CHROMIUM"):
        return path
    for name in ("chromium", "google-chrome", "chromium-browser", "msedge"):
        if path := shutil.which(name):
            return path
    for root in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        if root in os.environ:
            for relative in ("Google/Chrome/Application/chrome.exe",
                             "Microsoft/Edge/Application/msedge.exe"):
                path = Path(os.environ[root]) / relative
                if path.is_file():
                    return str(path)
    pytest.skip("Local Chromium required. Point ECNUCHAT_CHROMIUM to the browser executable.")


class DevTools:
    def __init__(self, socket):
        self.socket = socket
        self.sequence = 0

    def command(self, method, params=None, session=None):
        self.sequence += 1
        request = {"id": self.sequence, "method": method, "params": params or {}}
        if session:
            request["sessionId"] = session
        self.socket.send(json.dumps(request))
        while True:
            response = json.loads(self.socket.recv(timeout=15))
            if response.get("id") == self.sequence:
                assert "error" not in response, (method, response.get("error"))
                return response.get("result", {})


@contextmanager
def browser(profile):
    args = [find_browser(), f"--user-data-dir={profile}", "--remote-debugging-port=0",
            "--headless=new", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update", "--disable-sync",
            "--disable-extensions", "--disable-quic", "--proxy-server=http://127.0.0.1:9",
            "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1",
            "--allow-loopback-in-peer-connection", "--disable-features=WebRtcHideLocalIpsWithMdns",
            "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream",
            "--autoplay-policy=no-user-gesture-required", "--mute-audio",
            "--disable-renderer-backgrounding", "--disable-background-timer-throttling",
            "about:blank"]
    with subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as process:
        try:
            port_file = profile / "DevToolsActivePort"
            start = time.monotonic()
            while not port_file.exists():
                assert process.poll() is None, "Chromium exited during startup"
                assert time.monotonic() - start < 20, "Timed out starting Chromium"
                time.sleep(0.1)
            port, path = port_file.read_text().splitlines()
            # A direct socket also keeps CDP local on machines with a system proxy.
            with (create_connection((LOOPBACK, int(port)), timeout=10) as tcp,
                  connect(f"ws://{LOOPBACK}:{port}{path}", sock=tcp, max_size=4_000_000) as ws):
                cdp = DevTools(ws)
                try:
                    yield cdp
                finally:
                    cdp.command("Browser.close")
                    process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()


class Page:
    def __init__(self, cdp, url, *, persistent=False, preload=""):
        options = {"url": "about:blank"}
        if not persistent:
            options.update(cdp.command("Target.createBrowserContext"))
        target = cdp.command("Target.createTarget", options)
        self.session = cdp.command("Target.attachToTarget", {**target, "flatten": True})["sessionId"]
        self.cdp = cdp
        self.command("Page.enable", {})
        self.command("Page.addScriptToEvaluateOnNewDocument", {"source": OBSERVE_MEDIA})
        if preload:
            self.command("Page.addScriptToEvaluateOnNewDocument", {"source": preload})
        navigation = self.command("Page.navigate", {"url": url})
        assert not navigation.get("errorText"), navigation.get("errorText")
        self.wait("document.querySelector('#status')?.textContent.includes('Ready')", "PWA startup")
        assert self.js("!!window.mediaProbe"), "Chromium did not initialize the media probe"

    def command(self, method, params):
        return self.cdp.command(method, params, self.session)

    def js(self, expression):
        result = self.command("Runtime.evaluate", {
            "expression": expression, "returnByValue": True, "awaitPromise": True, "userGesture": True,
        })
        assert "exceptionDetails" not in result, result.get("exceptionDetails")
        return result["result"].get("value")

    def wait(self, expression, label, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if value := self.js(expression):
                return value
            time.sleep(0.15)
        status = self.js("[location.href, document.title, ...['status', 'voice-status', 'messages'].map("
                         "id => document.getElementById(id)?.textContent)]")
        raise AssertionError(f"Timed out waiting for {label}. UI status: {status}")

    def fill(self, selector, value):
        self.js(f"document.querySelector({json.dumps(selector)}).value = {json.dumps(value)}")
        self.js(f"document.querySelector({json.dumps(selector)}).dispatchEvent(new Event('change'))")

    def click(self, selector):
        element = f"document.querySelector({json.dumps(selector)})"
        self.wait(f"{element}?.getClientRects().length && !{element}.disabled", selector)
        self.js(f"{element}.click()")

    def register(self, name, relay):
        self.fill("#username", name)
        self.fill("#relay-url", relay)
        self.click("#register-form button")
        self.wait("document.querySelector('#status').textContent.includes('Registered device with relay')",
                  "registration")
        device = self.js("document.querySelector('#profile').innerText.split('\\n')[0].trim().split(':').pop()")
        fingerprint = self.js("document.querySelector('#profile code').textContent")
        return {"username": name, "relay": relay, "device": device, "fingerprint": fingerprint}

    def add_friend(self, invite):
        self.fill("#invite", json.dumps(invite))
        self.click("#add-friend-form button")
        self.fill("#chat-friend", invite["username"])

    def send(self, recipient, message):
        self.fill("#message-text", message)
        self.click("#send-form button")
        recipient.wait(f"document.querySelector('#messages').textContent.includes({json.dumps(message)})",
                       "receipt of " + message)

    def fail_first_send(self, message):
        self.js("""(() => {
            const fetch = window.fetch;
            const alert = window.alert;
            window.fetch = (url, init) => {
                if (new URL(url, location.href).pathname.endsWith('/envelopes') && init?.method === 'POST') {
                    window.fetch = fetch;
                    return Promise.reject(new TypeError('test first envelope offline'));
                }
                return fetch(url, init);
            };
            window.alert = message => { window.sendError = message; window.alert = alert; };
        })()""")
        self.fill("#message-text", message)
        self.click("#send-form button")
        self.wait("window.sendError?.includes('test first envelope offline')", "reported send failure")


OBSERVE_MEDIA = Path(__file__).with_name("voice_browser_probe.js").read_text(encoding="utf-8")


def audio_stats(page):
    stats = page.wait("""(async () => {
        const s = await mediaProbe.audio();
        const audio = document.querySelector('#voice-audio');
        return s?.packets > 0 && s.bytes > 0 && s.samples > 0 &&
            audio.srcObject?.getAudioTracks().length && !audio.paused && s;
    })()""", "decoded and playing incoming audio")
    assert stats["dtls"] == "connected"
    assert all(ipaddress.ip_address(stats[key]).is_loopback for key in ("local", "remote")), stats
    return stats


def test_voice_browser():
    class RelayHandler(Handler):
        relay = Relay(MemoryStore())

    with (TemporaryDirectory(prefix="ecnu-pwa-") as temp, serve(RelayHandler) as relay,
          serve(partial(Assets, directory=PWA)) as pwa, browser(Path(temp)) as cdp):
        alice, bob = Page(cdp, pwa), Page(cdp, pwa)
        alice_invite = alice.register("alice_test", relay)
        bob_invite = bob.register("bob_test", relay)
        alice.add_friend(bob_invite)
        bob.add_friend(alice_invite)
        failed_message = "First envelope interrupted before relay"
        alice.fail_first_send(failed_message)
        alice.command("Page.reload", {})
        alice.wait("window.mediaProbe && !window.sendError && "
                   "document.querySelector('#status')?.textContent.includes('Ready')",
                   "sender to reload its saved session")
        alice.fill("#chat-friend", bob_invite["username"])
        alice.send(bob, "Before call from Alice")
        assert not bob.js(f"document.querySelector('#messages').textContent.includes({json.dumps(failed_message)})")
        bob.send(alice, "Before call from Bob")
        assert alice.js("!!document.querySelector('#voice-call')"), "PWA voice call button is missing"
        assert alice.js("document.querySelector('#voice-device').value") == bob_invite["device"]
        alice.click("#voice-call")
        bob.wait("!document.querySelector('#voice-answer').hidden", "incoming call")
        assert bob.js("mediaProbe.captureRequests") == 0, "Microphone requested before answering"
        bob.click("#voice-answer")
        for page in (alice, bob):
            page.wait("document.querySelector('#voice-status').textContent.includes('In call')",
                      "connected call")
        first = [audio_stats(page) for page in (alice, bob)]
        for name, page, previous in zip(("Alice", "Bob"), (alice, bob), first):
            page.wait(f"mediaProbe.audio().then(s => s.packets > {previous['packets']} && "
                      f"s.bytes > {previous['bytes']})", "incoming RTP counters to increase")
            current = audio_stats(page)
            print(f"{name} received {current['packets']} audio RTP packets, "
                  f"{current['bytes']} bytes, {current['samples']} decoded samples "
                  f"({current['local']} to {current['remote']}, DTLS connected)")
        alice.click("#voice-mute")
        assert alice.js("mediaProbe.tracks.every(track => !track.enabled)")
        alice.click("#voice-mute")
        assert alice.js("mediaProbe.tracks.every(track => track.enabled)")
        alice.click("#voice-hangup")
        for page in (alice, bob):
            page.wait("document.querySelector('#voice-status').textContent.toLowerCase().includes('ended')",
                      "hangup")
            page.wait("mediaProbe.released()", "closed connection, stopped capture and detached audio")
        bob.send(alice, "After hangup from Bob")
        previous_capture_requests = alice.js("mediaProbe.captureRequests")
        bob.click("#voice-call")
        alice.wait("!document.querySelector('#voice-decline').hidden", "return call")
        assert alice.js("mediaProbe.captureRequests") == previous_capture_requests
        alice.click("#voice-decline")
        for page in (alice, bob):
            page.wait("document.querySelector('#voice-status').textContent.toLowerCase().includes('declined')",
                      "call declined")
            page.wait("mediaProbe.released()", "resources released after decline")
        assert alice.js("mediaProbe.captureRequests") == previous_capture_requests
