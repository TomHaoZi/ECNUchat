"""Compare the full directory and warm cache using the Chromium chat form.

python -m v2.tests.benchmark_directory_cache --output docs/benchmarks/directory-cache-wire.json
"""

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from urllib.parse import urlsplit

from v2.relay.relay import Handler
from v2.tests.test_pq_reference_browser import (
    assert_messages, browser_and_assets, conversation, disconnected, form, poll, send_from_chat,
)


class CountedStream:
    """Count only bytes consumed or written by the HTTP handler, even on keep-alive."""

    def __init__(self, stream):
        self.stream = stream
        self.size = 0

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def readline(self, *args):
        data = self.stream.readline(*args)
        self.size += len(data)
        return data

    def read(self, *args):
        data = self.stream.read(*args)
        self.size += len(data)
        return data

    def write(self, data):
        written = self.stream.write(data)
        self.size += written
        return written


@dataclass
class Exchange:
    route: str
    request_head: int
    declared_request_body: int
    guarded: bool
    hinted: bool = False
    declared_response_body: int = -1
    response_head: int = 0
    request_http: int = 0
    response_http: int = 0
    status: int = 0
    finished: Event = field(default_factory=Event)


ROUTES = {
    "/v1/devices", "/v1/devices/register", "/v1/bundles/fetch", "/v1/directory",
    "/v1/envelopes", "/v1/directory/envelopes", "/v1/inbox", "/v1/inbox/count",
}


def measured_handler(exchanges):
    class Measured(Handler):
        def setup(self):
            super().setup()
            self.rfile = CountedStream(self.rfile)
            self.wfile = CountedStream(self.wfile)

        def handle_one_request(self):
            self.rfile.size = self.wfile.size = 0
            self.exchange = None
            try:
                super().handle_one_request()
            finally:
                if self.exchange:
                    self.exchange.request_http = self.rfile.size
                    self.exchange.response_http = self.wfile.size
                    self.exchange.finished.set()

        def parse_request(self):
            if not super().parse_request():
                return False
            path = urlsplit(self.path).path
            route = self.command + " " + (path if path in ROUTES else "<other>")
            self.exchange = Exchange(route, self.rfile.size, int(self.headers.get("Content-Length", 0)),
                                     bool(self.headers.get("X-Directory-Version")))
            exchanges.append(self.exchange)
            return True

        def _send_json(self, status, obj):
            self.exchange.hinted = self.exchange.route == "GET /v1/inbox" and bool(obj.get("directory_version"))
            return super()._send_json(status, obj)

        def send_response(self, code, message=None):
            self.exchange.status = code
            return super().send_response(code, message)

        def send_header(self, name, value):
            if name.lower() == "content-length":
                self.exchange.declared_response_body = int(value)
            return super().send_header(name, value)

        def end_headers(self):
            super().end_headers()
            self.exchange.response_head = self.wfile.size

    return Measured


def summarize(exchanges, *, routes=True):
    totals, by_route = Counter(), {}
    for item in exchanges:
        assert item.finished.wait(5), "relay did not finish HTTP exchange"
        assert 200 <= item.status < 300, (item.route, item.status)
        request_body = item.request_http - item.request_head
        response_body = item.response_http - item.response_head
        assert (request_body, response_body) == (item.declared_request_body, item.declared_response_body)
        sizes = {
            "calls": 1, "request_body_bytes": request_body, "response_body_bytes": response_body,
            "body_bytes": request_body + response_body,
            "request_http_bytes": item.request_http, "response_http_bytes": item.response_http,
            "http_bytes": item.request_http + item.response_http,
        }
        totals.update(sizes)
        by_route.setdefault(item.route, Counter()).update(sizes)
    result = dict(totals)
    if routes:
        result["routes"] = dict(sorted(by_route.items()))
    return result


def measure(clients, cached):
    exchanges = []
    with conversation(clients, directory_cache=cached, handler_class=measured_handler(exchanges)) as setup:
        peers, relay, posts, _ = setup
        alice, bob = (page for page, _ in peers)
        start = len(exchanges)
        alice.add_friend(peers[1][1])
        send_from_chat(alice, 0)
        poll(peers, 1)
        poll(peers, 0)
        assert_messages(peers, 1, [0])
        assert [form(body) for body, _ in posts] == ["full", "ack"]
        warm_start = len(exchanges)
        with disconnected(bob):
            for i in range(1, 11):
                send_from_chat(alice, i)
            invite = peers[1][1]
            assert relay.inbox_count(invite["username"], invite["device"])["queued"] == 10
        polls_start = len(exchanges)
        poll(peers, 1)
        poll(peers, 0)
        assert_messages(peers, 1, range(11))
        assert_messages(peers, 0, range(11))
        assert [form(body) for body, _ in posts[2:]] == ["reference"] * 10

        cold = exchanges[start:warm_start]
        burst = exchanges[warm_start:]
        sends = exchanges[warm_start:polls_start]
        polls = exchanges[polls_start:]
        all_routes = Counter(item.route for item in burst)
        post_route = "POST /v1/directory/envelopes" if cached else "POST /v1/envelopes"
        assert all_routes[post_route] == 10 and all_routes["GET /v1/inbox"] == 2, all_routes
        assert all_routes["GET /v1/devices"] == (0 if cached else 10), all_routes
        assert all_routes["GET /v1/directory"] == 0, all_routes
        assert sum(item.guarded for item in sends) == (10 if cached else 0)
        hints = sum(item.hinted for item in polls)
        assert hints == (1 if cached else 0), hints
        return {
            "cold_first_contact": summarize(cold),
            "confirmed_burst_including_delivery": summarize(burst),
            "sender_while_receiver_offline": summarize(sends, routes=False),
            "two_inbox_polls_after_reconnection": summarize(polls, routes=False),
            "delivered_hybrid_reference_messages": 10,
            "version_guarded_burst_posts": sum(item.guarded for item in sends),
            "burst_inbox_responses_with_directory_version": hints,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with browser_and_assets() as clients:
        report = {
            "browser": clients[0].command("Browser.getVersion")["product"],
            "workload": "Two isolated Chromium profiles, one hybrid device each, localhost HTTP/1.1. "
                        "Both groups enable PQ references. Each group starts with freshly registered profiles. "
                        "The baseline uses dircache=0 on both clients. The cache group uses production defaults.",
            "schedule": "Cold first contact runs from adding the friend through the first 128-byte chat form "
                        "send, receiver decryption and sender receipt. Next, the sender submits ten 128-byte "
                        "ASCII messages via the chat form on the same confirmed chain with the receiver "
                        "disconnected. On reconnection the receiver polls once and the sender polls once. "
                        "Automatic five-second polls are suppressed for repeatability. CORS preflight cache "
                        "is browser-managed across each group's cold and warm phases.",
            "accounting": "Counts bytes read from and written to the loopback relay's HTTP streams. Includes "
                          "request/status lines, query strings, headers, CRLFs, CORS OPTIONS and bodies. "
                          "Body bytes are checked against HTTP Content-Length. Excludes registration before "
                          "friend-add, serving PWA assets, DevTools, and TCP/IP/link-layer overhead. The relay "
                          "uses no TLS or HTTP compression. Only aggregate sizes, counts and route templates "
                          "are exported. Exact sizes or preflight counts can vary between runs.",
        }
        for cached, label in ((False, "full_directory_per_send"), (True, "directory_cache")):
            report[label] = measure(clients, cached)
            result = report[label]["confirmed_burst_including_delivery"]
            print(label, result["body_bytes"], "body bytes;", result["http_bytes"], "HTTP bytes", flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
