"""Local chat-form comparison. Run with python -m v2.tests.benchmark_three_schemes."""

import hashlib
import json
import platform
from pathlib import Path

from v2.tests.benchmark_directory_cache import measured_handler, summarize
from v2.tests.test_pq_reference_browser import (
    browser_and_assets, conversation, disconnected, message, poll, send_from_chat,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/benchmarks/three-schemes-wire.json"
# (ML-KEM, authenticated references, versioned directory cache)
ARMS = {
    "A": (False, False, False), "B": (True, False, False), "C": (True, True, True),
    "D": (True, True, False), "E": (True, False, True), "F": (False, False, True),
}


def run_arm(clients, arm):
    hybrid, refs, cache = ARMS[arm]
    exchanges = []
    with conversation(clients, (refs, refs), hybrid=hybrid, directory_cache=cache,
                      handler_class=measured_handler(exchanges)) as setup:
        peers, relay, posts, _ = setup
        alice, bob = [page for page, _ in peers]
        start = len(exchanges)
        alice.add_friend(peers[1][1])
        send_from_chat(alice, 0)
        poll(peers, 1)
        poll(peers, 0)
        assert len(posts) == 1 + int(refs)
        assert bool(posts[0][0]["pq_ct"]) == hybrid and posts[0][0]["x3dh"]
        if refs:
            assert posts[1][0]["message_type"] == "pq_ack_v1"
        warm_start = len(exchanges)
        data_start = len(posts)
        with disconnected(bob):
            for i in range(1, 11):
                send_from_chat(alice, i)
            address = peers[1][1]
            assert relay.inbox_count(address["username"], address["device"])["queued"] == 10
        poll(peers, 1)
        poll(peers, 0)
        for page in (alice, bob):
            history = page.js("state.messages.map(m => [m.text,m.tag])")
            assert [m[0] for m in history] == [message(i) for i in range(11)]
            assert all(("hybrid" if hybrid else "classical") in m[1] for m in history)
        burst = posts[data_start:]
        assert len(burst) == 10
        assert all(not body["x3dh"] and bool(body.get("pq_ref")) == refs
                   and bool(body.get("pq_ct")) == (hybrid and not refs) for body, _ in burst)
        warm = summarize(exchanges[warm_start:])
        assert warm["routes"].get("GET /v1/devices", {}).get("calls", 0) == (0 if cache else 10)
        assert sum(item.guarded for item in exchanges[warm_start:]) == (10 if cache else 0)
        return {"arm": arm, "cold": summarize(exchanges[start:warm_start]), "warm": warm,
                "warm_envelope_request_bytes": sum(n for _, n in burst), "delivered": 10}


def main():
    source = ["v2/pwa/app.js", "v2/pwa/crypto.js", "v2/pwa/crypto-pq.js", "v2/pwa/directory.js",
              "v2/relay/relay.py", "v2/tests/benchmark_three_schemes.py", "v2/tests/benchmark_directory_cache.py",
              "v2/tests/test_pq_reference_browser.py", "v2/tests/test_voice_browser.py"]
    report = {"platform": platform.platform(), "python": platform.python_version(), "arms": ARMS,
              "order": "Six cyclic orders, one fresh browser process per block; new relay and two isolated profiles per arm.",
              "units": "raw HTTP/1.1 bytes at the loopback relay; cold=friend-add through message 0 and polls; "
                       "warm=ten 128-byte ASCII messages on the same chain plus two polls, excluding setup.",
              "sha256": {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in source}, "runs": []}
    labels = list(ARMS)
    for block in range(len(labels)):
        with browser_and_assets() as clients:
            report["browser"] = clients[0].command("Browser.getVersion")["product"]
            for position, arm in enumerate(labels[block:] + labels[:block]):
                run = run_arm(clients, arm)
                report["runs"].append(dict(block=block+1, position=position+1, **run))
                print(block+1, arm, run["warm"]["http_bytes"], flush=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
