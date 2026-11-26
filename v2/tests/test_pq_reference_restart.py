"""Reopen both the browser's on-disk profiles and a real SQLite-backed relay."""

import json
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from functools import partial
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory

from v2.tests.test_pq_reference_browser import assert_messages, poll, send
from v2.tests.test_voice_browser import Assets, LOOPBACK, PWA, Page, browser, serve


@contextmanager
def running_relay(directory, port):
    command = [sys.executable, str(PWA.parent / "relay" / "relay.py"), "--host", LOOPBACK,
               "--port", str(port), "--db", str(directory / "queue.sqlite")]
    with subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as process:
        try:
            deadline = time.monotonic() + 10
            while True:
                assert process.poll() is None, "Relay did not start"
                try:
                    with socket.create_connection((LOOPBACK, port), timeout=0.5):
                        break
                except OSError:
                    assert time.monotonic() < deadline, "Timed out waiting for local relay"
                    time.sleep(0.05)
            yield f"http://{LOOPBACK}:{port}"
        finally:
            process.terminate()
            process.wait(timeout=10)


def queued(port, peer):
    conn = HTTPConnection(LOOPBACK, port, timeout=2)
    try:
        conn.request("GET", f"/v1/inbox/count?recipient={peer['username']}:{peer['device']}")
        response = conn.getresponse()
        assert response.status == 200
        return json.loads(response.read())["queued"]
    finally:
        conn.close()


def profiles(cdp, url):
    # Each device has its own named application profile in the persistent
    # browser context. Fetch only when the test explicitly delivers a packet.
    return [Page(cdp, f"{url}/?profile={name}", persistent=True,
                 preload="window.setInterval = () => 0") for name in ("alice", "bobby")]


def test_queued_reference_survives_browser_and_relay_process_restart():
    with (TemporaryDirectory(prefix="ecnu-pq-restart-") as temp,
          serve(partial(Assets, directory=PWA)) as url):
        directory = Path(temp)
        profile = directory / "browser"
        profile.mkdir()
        with socket.socket() as sock:
            sock.bind((LOOPBACK, 0))
            port = sock.getsockname()[1]
        with running_relay(directory, port) as relay, browser(profile) as cdp:
            pages = profiles(cdp, url)
            invites = [page.register(name, relay) for page, name in zip(pages, ("alice", "bobby"))]
            peers = list(zip(pages, invites))
            send(peers, 0, 0)
            poll(peers, 1)
            poll(peers, 0)
            pages[0].js("""const realPost = postEnvelope;
                window.postEnvelope = body => { window.lastForm = [!!body.pq_ref, !!body.pq_ct];
                    return realPost(body); };""")
            send(peers, 0, 1)
            assert pages[0].js("window.lastForm") == [True, False]
            assert queued(port, invites[1]) == 1

        # Chromium may leave the previous ephemeral debugging port on disk.
        (profile / "DevToolsActivePort").unlink(missing_ok=True)
        with running_relay(directory, port), browser(profile) as cdp:
            peers = list(zip(profiles(cdp, url), invites))
            assert queued(port, invites[1]) == 1
            poll(peers, 1)
            assert_messages(peers, 1, [0, 1])
            assert queued(port, invites[0]) == 0
            send(peers, 0, 2)
            poll(peers, 1)
            assert_messages(peers, 1, [0, 1, 2])
            assert queued(port, invites[0]) == 0
