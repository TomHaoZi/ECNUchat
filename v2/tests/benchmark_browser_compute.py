"""Measure combined renderer main-thread task time for the local chat workload."""

import json
import platform

from v2.tests.benchmark_three_schemes import ARMS, ROOT
from v2.tests.test_pq_reference_browser import (
    browser_and_assets, conversation, disconnected, message, poll, send_from_chat,
)


def renderer_ms(peers):
    total = 0.0
    for page, _ in peers:
        metrics = page.command("Performance.getMetrics", {})["metrics"]
        total += next(item["value"] for item in metrics if item["name"] == "TaskDuration")
    return 1000 * total


def measure(clients, arm):
    hybrid, refs, cache = ARMS[arm]
    with conversation(clients, (refs, refs), hybrid=hybrid, directory_cache=cache) as setup:
        peers, relay, posts, _ = setup
        for page, _ in peers:
            page.command("Performance.enable", {"timeDomain": "threadTicks"})
        alice, bob = [page for page, _ in peers]
        start = renderer_ms(peers)
        alice.add_friend(peers[1][1])
        send_from_chat(alice, 0)
        poll(peers, 1)
        poll(peers, 0)
        established = renderer_ms(peers)
        assert len(posts) == 1 + int(refs)
        with disconnected(bob):
            for i in range(1, 11):
                send_from_chat(alice, i)
            address = peers[1][1]
            assert relay.inbox_count(address["username"], address["device"])["queued"] == 10
        poll(peers, 1)
        poll(peers, 0)
        finished = renderer_ms(peers)
        assert finished > established > start
        for page, _ in peers:
            assert page.js("state.messages.map(m => m.text)") == [message(i) for i in range(11)]
        assert all(bool(body.get("pq_ref")) == refs and bool(body.get("pq_ct")) == (hybrid and not refs)
                   for body, _ in posts[1 + int(refs):])
        return {"arm": arm, "cold_ms": established - start, "warm_ten_ms": finished - established}


def main():
    data = {"metric": "Sum of Chrome CDP Performance.TaskDuration, threadTicks, both renderer main threads (ms).",
            "includes": "JS, DOM, UI and test-driver page tasks. Excludes network wait, native workers and relay CPU.",
            "platform": platform.platform(), "arms": ARMS, "runs": []}
    labels = list(ARMS)
    for block in range(len(labels)):
        with browser_and_assets() as clients:
            data["browser"] = clients[0].command("Browser.getVersion")["product"]
            for position, arm in enumerate(labels[block:] + labels[:block]):
                row = measure(clients, arm)
                data["runs"].append(dict(block=block + 1, position=position + 1, **row))
                print(block + 1, arm, round(row["warm_ten_ms"], 2), flush=True)
    output = ROOT / "docs/benchmarks/three-schemes-renderer.json"
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
