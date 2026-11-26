"""Offline, two-endpoint Python v1 direct-message benchmark. Run with --help."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from itertools import cycle, islice, repeat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cryptography
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.client import ChatEngine
from src.prekeys import (
    MLKEM_SUPPORTED, OneTimePrekey, PqOneTimePrekey, generate_identity,
    generate_mlkem768, generate_x25519, sign_pq_opk,
)
from src.protocol import b64d, b64e, dumps, loads
from src.store import _state_to_json

BURST = 128  # timed deliveries per established session


class MemoryStore:
    """Pinned peer identity and temporary outbox. Sessions already live in ChatEngine."""

    def __init__(self, peer):
        self.pinned = {peer.username: (peer.ik_sign_pub, peer.ik_dh_pub, peer.pq_pub)}
        self.outbox = {}

    def load_peer(self, peer):
        return self.pinned[peer]

    def get_conversation_privacy(self, conv):
        return "low"

    def load_outbox(self, peer):
        return self.outbox.get(peer)

    def save_session_with_outbox(self, peer, state, payload):
        self.outbox[peer] = payload

    def delete_outbox(self, peer):
        del self.outbox[peer]

    def save_identity(self, identity):
        pass

    def save_session(self, peer, state):
        pass


class OfflineClient(ChatEngine):
    """Measure one forwarded envelope, matching ChatServer.on_envelope's JSON."""

    async def request(self, obj, *expect):
        if obj["type"] == "fetch_bundle":
            if obj.get("consume_pq_opk"):
                return self.bundle
            # The classical client's upgrade probe reads these fields on every send.
            if self.identity.pq_pub is not None:
                raise AssertionError("Unexpected upgrade probe in a hybrid session")
            return {"pq_pub": None, "pq_sig": None}
        if obj["type"] != "envelope":
            raise AssertionError(f"Unexpected request {obj['type']}")
        self.wire = dumps(obj).encode("utf-8")
        return {"type": "envelope_ok"}


def registered_identities(hybrid):
    identities = [generate_identity(name) for name in ("alice", "bob")]
    if hybrid:
        return identities
    return [replace(x, pq_priv=None, pq_pub=None, pq_sig=None, pq_opks=[]) for x in identities]


def new_pair(identities):
    alice, bob = identities
    opk = OneTimePrekey(*generate_x25519())
    pq_opk = None
    if bob.pq_priv is not None:
        seed, pub = generate_mlkem768()
        pq_opk = PqOneTimePrekey(seed, pub, sign_pq_opk(bob.ik_sign_priv, pub, bob.username))
    # Each new handshake gets distinct one-time keys. Keep a pre-provisioned reserve
    # so that replenishment (registration/directory work) never enters these timings.
    bob = replace(bob, opks=[opk, *bob.opks], pq_opks=([pq_opk] if pq_opk else []) + bob.pq_opks)
    a = OfflineClient(alice.username, "", MemoryStore(bob), alice)
    b = OfflineClient(bob.username, "", MemoryStore(alice), bob)
    b.peer_keys.update(b.store.pinned)
    a.bundle = {
        "ik_sign_pub": b64e(bob.ik_sign_pub), "ik_dh_pub": b64e(bob.ik_dh_pub),
        "spk_pub": b64e(bob.spk.pub), "spk_sig": b64e(bob.spk.signature),
        "opk": b64e(opk.pub), "pq_pub": b64e(bob.pq_pub), "pq_sig": b64e(bob.pq_sig),
        "pq_opk": b64e(pq_opk.pub) if pq_opk else None,
        "pq_opk_sig": b64e(pq_opk.signature) if pq_opk else None,
    }
    return a, b


async def deliver(sender, recipient, text):
    await sender._send_one(recipient.username, text, group=None, kind="chat")
    envelope = loads(sender.wire)
    received, group, kind, _, extra = await recipient._decrypt_envelope(
        envelope["from"], envelope["payload"]
    )
    if (received, group, kind, extra["privacy"]) != (text, None, "chat", "low"):
        raise AssertionError("v1 message did not round trip")
    return len(sender.wire)


def control(key=None):
    cipher = AESGCM(key) if key is not None else None

    async def exchange(sender, recipient, text):
        # Same logical body as ChatEngine._send_one for a normal direct message.
        body = {"v": 1, "text": text, "group": None, "kind": "chat", "gstate": None,
                "thread": None, "thread_title": None, "privacy": "low"}
        if cipher is None:
            payload = body
        else:
            nonce = os.urandom(12)
            aad = (sender + ":" + recipient).encode()
            ct = cipher.encrypt(nonce, dumps(body).encode(), aad)
            payload = {"kind": "chat", "nonce": b64e(nonce), "ciphertext": b64e(ct)}
        wire = dumps({"type": "envelope", "from": sender, "to": recipient, "payload": payload}).encode()
        env = loads(wire)
        payload = env["payload"]
        if cipher is None:
            recovered = payload
        else:
            aad = (env["from"] + ":" + env["to"]).encode()
            recovered = json.loads(cipher.decrypt(b64d(payload["nonce"]), b64d(payload["ciphertext"]), aad))
        if recovered != body:
            raise AssertionError("Control message did not round trip")
        return len(wire)

    return exchange


async def prepare(mode, scenario, count, text, identities):
    if mode in ("plaintext_json", "aes256gcm_psk"):
        key = AESGCM.generate_key(bit_length=256) if mode == "aes256gcm_psk" else None
        return control(key), repeat(("alice", "bob"), count)
    if scenario == "first":
        return deliver, [new_pair(identities[mode]) for _ in range(count)]
    pairs = []
    for start in range(0, count, BURST):
        a, b = new_pair(identities[mode])
        await deliver(a, b, text)  # completed first message, outside the timed block
        steps = cycle(((b, a), (a, b))) if scenario == "alternating" else repeat((a, b))
        pairs.extend(islice(steps, min(BURST, count - start)))
    return deliver, pairs


async def batch(case, count, identities):
    mode, scenario, nbytes = case
    text = "x" * nbytes
    exchange, pairs = await prepare(mode, scenario, count, text, identities)
    sizes = []
    wall0 = time.perf_counter_ns()
    cpu0 = time.process_time_ns()
    for sender, recipient in pairs:
        sizes.append(await exchange(sender, recipient, text))
    cpu = time.process_time_ns() - cpu0
    wall = time.perf_counter_ns() - wall0
    return {
        "messages": len(sizes), "wall_ns": wall, "process_cpu_ns": cpu,
        "wire_bytes_min": min(sizes), "wire_bytes_max": max(sizes), "wire_bytes_total": sum(sizes),
    }


async def state_probe(identities):
    def snapshot(a, b):
        # Only lengths leave this process. This is the actual pre-vault serialization.
        return {x.username: len(_state_to_json(x.sessions[y.username])) for x, y in ((a, b), (b, a))}

    result = {}
    for mode, ids in identities.items():
        observations = {}
        for scenario in ("one_way", "alternating"):
            a, b = new_pair(ids)
            await deliver(a, b, "x" * 128)
            expected = "pqopk" if mode == "v1_hybrid" else None
            if any(state.handshake_pq != expected for state in (a.sessions["bob"], b.sessions["alice"])):
                raise AssertionError("Wrong handshake branch")
            if len(b.identity.opks) != len(ids[1].opks) or len(b.identity.pq_opks) != len(ids[1].pq_opks):
                raise AssertionError("Issued one-time key was not consumed")
            observations["after_first"] = snapshot(a, b)
            steps = cycle(((b, a), (a, b))) if scenario == "alternating" else repeat((a, b))
            for sender, recipient in islice(steps, 32):
                await deliver(sender, recipient, "x" * 128)
            observations["after_first_plus_32_" + scenario] = snapshot(a, b)
        result[mode] = observations
    return result


async def run(args):
    if not MLKEM_SUPPORTED:
        raise SystemExit("ML-KEM-768 is required. Use the project's ML-KEM-enabled Python environment.")
    identities = {name: registered_identities(name == "v1_hybrid") for name in ("v1_classical", "v1_hybrid")}
    counts = {}
    for size in (128, 4096):
        counts["plaintext_json", "message", size] = 65536 if size == 128 else 16384
        counts["aes256gcm_psk", "message", size] = 32768 if size == 128 else 8192
        for mode in identities:
            counts[mode, "one_way", size] = 8192 if size == 128 else 4096
    for mode in identities:
        counts[mode, "first", 128] = 512
        counts[mode, "alternating", 128] = 2048

    rng = random.Random(7319)
    cases = list(counts)
    measurements = {case: [] for case in cases}
    state_sizes = await state_probe(identities)
    for case in cases:
        await batch(case, 2, identities)  # including controls and 4 KiB serialization
    for trial in range(1 if args.smoke else args.batches):
        rng.shuffle(cases)
        for case in cases:
            sample = await batch(case, 2 if args.smoke else counts[case], identities)
            measurements[case].append(sample)
        print(f"Finished batch {trial + 1}", file=sys.stderr, flush=True)

    rows = []
    for (mode, scenario, nbytes), samples in sorted(measurements.items()):
        def median_us(clock):
            return statistics.median(s[clock] / s["messages"] / 1000 for s in samples)

        rows.append({
            "mode": mode, "scenario": scenario, "text_bytes": nbytes,
            "median_wall_us_per_message": median_us("wall_ns"),
            "median_cpu_us_per_message": median_us("process_cpu_ns"),
            "samples": samples,
        })
    source_paths = ("scripts/benchmark_v1.py", "src/client.py", "src/protocol.py", "src/prekeys.py",
                    "src/x3dh.py", "src/double_ratchet.py", "src/store.py")
    return {
        "finished_utc": datetime.now(timezone.utc).isoformat(), "smoke": args.smoke,
        "os": platform.platform(), "python": platform.python_version(), "cpu": platform.processor(),
        "cryptography": cryptography.__version__, "openssl": backend.openssl_version_text(),
        "timing": "Median of batch totals divided by successful messages. Both endpoints in one process.",
        "clock_resolution_s": {k: time.get_clock_info(k).resolution for k in ("perf_counter", "process_time")},
        "profiles": "first = registered identities, fresh OPK (also PQOPK in hybrid); one_way = A to B; alternating = B to A then A to B. Established bursts are at most 128 messages after an untimed A-to-B bootstrap. PSK/plain controls have no handshake or ratchet.",
        "scope": "Includes source v1 send/decrypt, authentication, JSON/base64 and per-delivery correctness checks. Prebuilt directory response, warm pinned identities; excludes registration, prekey provisioning, database, UI, server, networking and requests/acks.",
        "wire_scope": "One relay-to-recipient application JSON envelope in UTF-8. Excludes other messages, WebSocket framing and transport.",
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in source_paths},
        "state_json_bytes_per_endpoint": state_sizes, "results": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", type=int, default=7, help="independent batch repetitions (default 7)")
    parser.add_argument("--smoke", action="store_true", help="test all paths with two timed messages per case")
    parser.add_argument("--output", type=Path, help="write aggregate measurements and raw sample totals to JSON")
    args = parser.parse_args()
    if args.batches < 1:
        parser.error("--batches must be positive")
    output = json.dumps(asyncio.run(run(args)), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
