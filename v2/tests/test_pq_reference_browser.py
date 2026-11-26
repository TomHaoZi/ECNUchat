"""Hybrid envelope tests on two isolated Chromium profiles and the loopback relay.

Run the size benchmark from the repository root with
python -m v2.tests.test_pq_reference_browser --output docs/benchmarks/pq-reference-wire.json
"""

import argparse
import json
from collections import Counter
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from v2.relay.relay import Handler, MemoryStore, Relay
from v2.tests.test_voice_browser import Assets, PWA, Page, browser, serve


LEGACY_FIELDS = {
    "sender", "recipient", "ciphertext", "protocol_version", "message_type",
    "dh_pub", "n", "pn", "nonce", "kind", "x3dh", "pq_ct",
}


def message(index):
    return f"Message {index:03d} ".ljust(128, "x")


@contextmanager
def browser_and_assets():
    with (TemporaryDirectory(prefix="ecnu-pq-ref-") as temp, browser(Path(temp)) as cdp,
          serve(partial(Assets, directory=PWA)) as pwa):
        yield cdp, pwa


@pytest.fixture(scope="module")
def clients():
    with browser_and_assets() as setup:
        yield setup


def reload_page(page):
    page.js("window.beforeTestReload = true")
    page.command("Page.reload", {})
    page.wait("!window.beforeTestReload && window.manualInbox && "
              "document.querySelector('#status')?.textContent.includes('Ready')", "reloaded profile")


@contextmanager
def conversation(clients, enabled=(True, True), traffic=None, *, directory_cache=True, handler_class=Handler,
                 hybrid=True):
    cdp, pwa = clients
    posts = []
    inbox_bytes = []
    relay = Relay(MemoryStore())

    class Capture(handler_class):
        def _read_json(self):
            body = super()._read_json()
            if self.path in ("/v1/envelopes", "/v1/directory/envelopes"):
                # Chromium supplies Content-Length for the exact UTF-8 request body.
                # The production relay has already consumed and parsed those bytes.
                posts.append((body, int(self.headers["Content-Length"])))
            return body

        def _send_json(self, status, obj):
            self.nonempty_inbox = self.path.startswith("/v1/inbox?") and bool(obj.get("envelopes"))
            return super()._send_json(status, obj)

        def send_header(self, name, value):
            if name == "Content-Length" and traffic is not None and self.path.startswith("/v1/"):
                traffic.append((self.command + " " + self.path.partition("?")[0],
                                int(self.headers.get("Content-Length") or 0), int(value)))
            if name == "Content-Length" and getattr(self, "nonempty_inbox", False):
                inbox_bytes.append(int(value))
                self.nonempty_inbox = False
            return super().send_header(name, value)

    Capture.relay = relay
    contexts = []
    with serve(Capture) as url:
        try:
            peers = []
            for name, refs in zip(("alice", "bobby"), enabled):
                url_params = f"profile={name}" + ("" if refs else "&pqrefs=0")
                if not directory_cache:
                    url_params += "&dircache=0"
                page = Page(cdp, f"{pwa}/?{url_params}")
                contexts.append(page.command("Target.getTargetInfo", {})["targetInfo"]["browserContextId"])
                if not hybrid:
                    # Exercise the PWA's classical-only path on two fresh, unregistered profiles.
                    page.command("Network.enable", {})
                    page.command("Network.setBypassServiceWorker", {"bypass": True})
                    page.command("Network.setBlockedURLs", {"urls": ["*/crypto-pq.js"]})
                # Keep real inbox operations, controlling only when the timer polls.
                # Installing this before reload also covers subsequent persistence tests.
                page.command("Page.addScriptToEvaluateOnNewDocument", {"source": """
                    const nativeInterval = window.setInterval.bind(window);
                    window.setInterval = (callback, delay, ...args) =>
                        delay === 5000 ? 0 : nativeInterval(callback, delay, ...args);
                    window.manualInbox = true;
                """})
                reload_page(page)
                assert page.js("typeof ECNUcryptoPQ !== 'undefined'") == hybrid
                invite = page.register(name, url)
                registered = relay.list_devices(name)["devices"][0]["public_keys"]
                assert bool(registered.get("pq_pub")) == hybrid
                assert (registered.get("pq_refs") == 1) == refs
                peers.append((page, invite))
            yield peers, relay, posts, inbox_bytes
        finally:
            for context in contexts:
                cdp.command("Target.disposeBrowserContext", {"browserContextId": context})


def send(peers, sender, index):
    page = peers[sender][0]
    invite = peers[1 - sender][1]
    args = ", ".join(map(json.dumps, (invite["username"], invite["device"], message(index), "chat")))
    tag = page.js(f"withRatchet(() => sendToDevice({args}))")
    assert "hybrid" in tag


def poll(peers, index):
    peers[index][0].js("fetchInbox()")


def assert_messages(peers, index, expected):
    actual = peers[index][0].js("state.messages.map(m => [m.text, m.tag])")
    assert all("hybrid" in tag for _, tag in actual), actual
    assert [text for text, _ in actual] == [message(i) for i in expected]


def pop(relay, peer):
    invite = peer[1]
    return relay.fetch_inbox(invite["username"], invite["device"])["envelopes"]


def form(body):
    if body["message_type"] == "pq_ack_v1":
        return "ack"
    if body.get("pq_ct"):
        return "full"
    assert body.get("pq_ref"), "missing hybrid ciphertext and reference"
    return "reference"


def test_lost_initial_ack_and_reordered_references(clients):
    with conversation(clients) as (peers, relay, posts, _):
        send(peers, 0, 0)
        dropped, = pop(relay, peers[1])  # HTTP succeeded but first inbox delivery was lost.
        assert dropped.get("x3dh") and form(dropped) == "full"
        reload_page(peers[0][0])
        send(peers, 0, 1)
        assert posts[-1][0]["x3dh"] == dropped["x3dh"]
        assert posts[-1][0]["pq_ct"] == dropped["pq_ct"]
        poll(peers, 1)
        lost_ack, = pop(relay, peers[0])
        assert form(lost_ack) == "ack"
        assert_messages(peers, 1, [1])

        send(peers, 0, 2)
        assert posts[-1][0].get("x3dh") and form(posts[-1][0]) == "full"
        poll(peers, 1)
        poll(peers, 0)
        assert_messages(peers, 0, [])
        for page, _ in peers:
            reload_page(page)

        marker = len(posts)
        send(peers, 0, 3)
        send(peers, 0, 4)
        batch = pop(relay, peers[1])
        assert len(batch) == 2
        for body in reversed(batch):
            relay.store.enqueue(body)
        poll(peers, 1)
        assert_messages(peers, 1, [1, 2, 4, 3])
        assert [form(body) for body, _ in posts[marker:]] == ["reference", "reference"]
        assert all(not body.get("x3dh") and not body.get("pq_ct") for body, _ in posts[marker:])

        send(peers, 1, 5)
        poll(peers, 0)
        poll(peers, 1)
        send(peers, 0, 6)
        assert form(posts[-1][0]) == "full", "a new sending chain needs its own confirmation"
        poll(peers, 1)
        assert_messages(peers, 0, [5])
        assert_messages(peers, 1, [1, 2, 4, 3, 6])


def test_storage_failure_before_receipt(clients):
    with conversation(clients) as (peers, _, posts, _):
        bob = peers[1][0]
        bob.js("""(() => {
            const setItem = Storage.prototype.setItem;
            Storage.prototype.setItem = function (key, value) {
                if (key === STORE_KEY) throw new DOMException('test storage full', 'QuotaExceededError');
                return setItem.call(this, key, value);
            };
        })()""")
        send(peers, 0, 1)
        poll(peers, 1)
        assert [form(body) for body, _ in posts] == ["full"]
        assert bob.js("Object.keys(JSON.parse(localStorage.getItem(STORE_KEY)).sessions).length") == 0
        reload_page(bob)  # Back to functioning storage with the last durable profile.
        send(peers, 0, 2)
        assert posts[-1][0].get("x3dh") and form(posts[-1][0]) == "full"
        poll(peers, 1)
        poll(peers, 0)
        send(peers, 0, 3)
        poll(peers, 1)
        assert_messages(peers, 1, [2, 3])
        assert [form(body) for body, _ in posts] == ["full", "full", "ack", "reference"]


@pytest.mark.parametrize("enabled", [(True, False), (False, True)])
def test_peer_without_extension_keeps_legacy_hybrid(clients, enabled):
    with conversation(clients, enabled) as (peers, _, posts, _):
        for sender, index in ((0, 1), (0, 2), (1, 3)):
            send(peers, sender, index)
            poll(peers, 1 - sender)
            poll(peers, sender)
        assert_messages(peers, 0, [3])
        assert_messages(peers, 1, [1, 2])
        assert [form(body) for body, _ in posts] == ["full"] * 3
        assert all(set(body) == LEGACY_FIELDS for body, _ in posts)
        assert not posts[1][0].get("x3dh")


def totals(posts, inbox_bytes):
    sizes = Counter()
    histogram = Counter()
    for body, length in posts:
        kind = form(body)
        sizes[kind] += length
        label = "initial_full" if body.get("x3dh") else kind
        histogram[(label, length)] += 1
    return {
        "total_bytes": sum(sizes.values()),
        "data_bytes": sizes["full"] + sizes["reference"],
        "ack_bytes": sizes["ack"],
        "nonempty_inbox_response_bytes": sum(inbox_bytes),
        "posts": [{"type": kind, "body_bytes": length, "count": count}
                  for (kind, length), count in sorted(histogram.items())],
    }


OFFLINE_SETUPS = {
    "offline_burst": (),                 # First contact
    "offline_after_confirmation": (0,),  # Continue the same sending chain
    "offline_after_reply": (0, 1),       # The reply caused a DH ratchet step
}


@contextmanager
def disconnected(bob):
    bob.command("Network.enable", {})
    conditions = {"latency": 0, "downloadThroughput": -1, "uploadThroughput": -1}
    bob.command("Network.emulateNetworkConditions", {**conditions, "offline": True})
    try:
        assert bob.js("""fetch(relayBase() + '/v1/inbox/count?recipient=' + encodeURIComponent(meAddress()),
            {cache: 'no-store'}).then(() => false, () => true)"""), "Receiver could still reach the relay"
        yield
    finally:
        bob.command("Network.emulateNetworkConditions", {**conditions, "offline": False})


def measure_offline(peers, relay, posts, inbox_bytes, refs, scenario):
    expected = [[], []]
    for sender in OFFLINE_SETUPS[scenario]:
        send(peers, sender, 0)
        poll(peers, 1 - sender)
        poll(peers, sender)
        expected[1 - sender].append(0)
    for index in (0, 1):
        assert_messages(peers, index, expected[index])
    start_posts, start_inbox = len(posts), len(inbox_bytes)
    bob, address = peers[1]
    with disconnected(bob):
        for index in range(1, 11):
            send(peers, 0, index)
        assert relay.inbox_count(address["username"], address["device"])["queued"] == 10
        assert_messages(peers, 1, expected[1])
    poll(peers, 1)
    poll(peers, 0)
    expected[1].extend(range(1, 11))
    for index in (0, 1):
        assert_messages(peers, index, expected[index])

    burst = posts[start_posts:]
    compact = refs and scenario == "offline_after_confirmation"
    forms = Counter(form(body) for body, _ in burst)
    assert forms == Counter({"reference" if compact else "full": 10, "ack": 10 if refs and not compact else 0})
    initials = (10 if refs else 1) if scenario == "offline_burst" else 0
    assert sum(bool(body.get("x3dh")) for body, _ in burst) == initials
    result = totals(burst, inbox_bytes[start_inbox:])

    # After reconnection, verify the next message is compact even if
    # the burst was on a previously unconfirmed chain. Exclude this probe from the totals.
    send(peers, 0, 11)
    assert form(posts[-1][0]) == ("reference" if refs else "full")
    poll(peers, 1)
    assert_messages(peers, 1, expected[1] + [11])
    return {10: result}


def send_from_chat(page, index):
    text = message(index)
    page.fill("#message-text", text)
    page.click("#send-form button")
    page.wait(f"state.messages.some(m => m.dir === 'out' && m.text === {json.dumps(text)})",
              f"UI send {index} completed")


def measure_confirmed_chat_burst(clients, refs):
    traffic = []
    with conversation(clients, (refs, refs), traffic, directory_cache=False) as (peers, _, posts, inbox_bytes):
        alice = peers[0][0]
        alice.add_friend(peers[1][1])
        send_from_chat(alice, 0)
        poll(peers, 1)
        poll(peers, 0)
        assert_messages(peers, 1, [0])
        traffic.clear()
        start_posts, start_inbox = len(posts), len(inbox_bytes)
        with disconnected(peers[1][0]):
            for index in range(1, 11):
                send_from_chat(alice, index)
        poll(peers, 1)
        poll(peers, 0)
        assert_messages(peers, 1, range(11))
        burst = posts[start_posts:]
        assert [form(body) for body, _ in burst] == ["reference" if refs else "full"] * 10
        routes = {}
        for route, sent, received in traffic:
            row = routes.setdefault(route, {"calls": 0, "request_bytes": 0, "response_bytes": 0})
            row["calls"] += 1
            row["request_bytes"] += sent
            row["response_bytes"] += received
        assert routes["GET /v1/devices"]["calls"] == 10
        assert routes["GET /v1/inbox"]["calls"] == 2
        assert routes["POST /v1/envelopes"]["request_bytes"] == sum(length for _, length in burst)
        return {
            "all_relay_body_bytes": sum(sent + received for _, sent, received in traffic),
            "envelopes": totals(burst, inbox_bytes[start_inbox:]),
            "routes": routes,
        }


def measure(clients, refs, scenario):
    with conversation(clients, (refs, refs), directory_cache=False) as (peers, relay, posts, inbox_bytes):
        if scenario in OFFLINE_SETUPS:
            return measure_offline(peers, relay, posts, inbox_bytes, refs, scenario)
        expected = [[], []]
        results = {}
        stop = 10 if scenario == "lost_first_ack" else 100
        for index in range(1, stop + 1):
            sender = (index - 1) % 2 if scenario == "alternating" else 0
            send(peers, sender, index)
            poll(peers, 1 - sender)
            expected[1 - sender].append(index)
            if scenario == "lost_first_ack" and index == 1 and refs:
                lost, = pop(relay, peers[sender])
                assert form(lost) == "ack"
            else:
                poll(peers, sender)
            if index in (1, 2, 10, 100):
                for endpoint in (0, 1):
                    assert_messages(peers, endpoint, expected[endpoint])
                results[index] = totals(posts, inbox_bytes)
        forms = Counter(form(body) for body, _ in posts)
        full = stop if (not refs or scenario == "alternating") else (2 if scenario == "lost_first_ack" else 1)
        assert forms["full"] == full and forms["reference"] == stop - full, forms
        assert forms["ack"] == (full if refs else 0), forms
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with browser_and_assets() as clients:
        report = {
            "browser": clients[0].command("Browser.getVersion")["product"],
            "body": "128 ASCII bytes; alice and bobby; one device each; new hybrid session per workload",
            "measurement": "Content-Length of real POST /v1/envelopes UTF-8 request bodies, both directions. "
                           "Includes x3dh and all ACKs, even a lost ACK. Nonempty inbox response bytes "
                           "are measured separately from HTTP Content-Length. Excludes other requests, "
                           "empty polls, HTTP headers, transport framing and compression.",
            "schedule": "Each data message is received before the sender consumes its ACK (if any). "
                        "In lost_first_ack only the first ACK is discarded after its POST. For offline cases "
                        "the receiver is disconnected in Chromium while ten messages queue. Burst totals include "
                        "all resulting receipts through reconnection. They exclude earlier setup messages and "
                        "a subsequent delivery probe. offline_burst starts fresh, offline_after_confirmation "
                        "follows one delivered A-to-B message and its receipt (if enabled), and "
                        "offline_after_reply additionally follows one delivered B-to-A reply and its receipt.",
            "cases": {},
            "confirmed_chat_ui_burst": {
                "measurement": "Ten sends using the chat form on an established sending chain. The receiver "
                               "reconnects and fetches once, followed by a sender inbox poll. Counts all relay "
                               "request and response bodies during the burst, excluding setup, HTTP headers "
                               "and transport framing. Both groups use dircache=0 for the original directory behavior.",
            },
        }
        for refs, name in ((False, "legacy"), (True, "references")):
            for scenario in ("same_direction", "alternating", "lost_first_ack", *OFFLINE_SETUPS):
                result = measure(clients, refs, scenario)
                report["cases"][f"{name}_{scenario}"] = result
                print(name, scenario, {n: r["total_bytes"] for n, r in result.items()}, flush=True)
            result = measure_confirmed_chat_burst(clients, refs)
            report["confirmed_chat_ui_burst"][name] = result
            print(name, "confirmed_chat_ui_burst", result["all_relay_body_bytes"], flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
