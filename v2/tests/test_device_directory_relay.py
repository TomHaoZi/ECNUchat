"""Exercise compact directories and conditional delivery over the relay's HTTP API."""

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest

from v2.relay.relay import Handler, MemoryStore, Relay, SQLiteStore


@contextmanager
def serving(store):
    class RelayHandler(Handler):
        relay = Relay(store)

    with ThreadingHTTPServer(("127.0.0.1", 0), RelayHandler) as server:
        thread = threading.Thread(target=server.serve_forever, args=(0.01,))
        thread.start()
        conn = HTTPConnection(*server.server_address, timeout=5)

        def request(method, path, body=None, headers=(), status=200):
            data = json.dumps(body).encode() if body is not None else b""
            conn.putrequest(method, path)
            conn.putheader("Content-Length", str(len(data)))
            for name, value in headers:
                conn.putheader(name, value)
            conn.endheaders(data)
            response = conn.getresponse()
            raw = response.read()
            assert response.status == status, (method, path, response.status, raw)
            return json.loads(raw) if raw else None, response.headers

        try:
            yield request
        finally:
            conn.close()
            server.shutdown()
            thread.join()
            if isinstance(store, SQLiteStore):
                store.conn.close()


@pytest.fixture(params=["memory", "sqlite"])
def request_api(request, tmp_path):
    store = MemoryStore() if request.param == "memory" else SQLiteStore(str(tmp_path / "relay.db"))
    with serving(store) as api:
        yield api


def register(api, device="phone", **fields):
    api("POST", "/v1/devices/register", {"username": "alice", "device": device, **fields})


def directory(api, username="alice"):
    result, headers = api("GET", "/v1/directory?username=" + username)
    assert headers["Cache-Control"] == "no-store"
    assert set(result) == {"username", "version", "devices"}
    assert result["username"] == username
    assert re.fullmatch("[a-f0-9]{64}", result["version"])
    return result


def test_directory_is_sorted_compact_and_preserves_both_opk_pools(request_api):
    api = request_api
    pk = {"ik_sign_pub": "sign", "ik_dh_pub": "dh", "pq_pub": "pq", "pq_refs": 1,
          "spk_pub": "spk", "opks": ["first", "second"],
          "pq_opks": [{"pub": "pq1", "sig": "s1"}, {"pub": "pq2", "sig": "s2"}]}
    register(api, "phone", identity_key="top", one_time_prekeys=pk["opks"], public_keys=pk)
    register(api, "desk", identity_key="old", public_keys=["legacy opaque value"])
    register(api, "bad", identity_key={"opaque": "value"},
             public_keys={"ik_sign_pub": ["malformed"], "pq_refs": "1"})
    full, _ = api("GET", "/v1/devices?username=alice")
    snapshot = directory(api)
    assert snapshot["devices"] == [
        {"device": "bad", "ik_sign_pub": None, "pq_refs": False},
        {"device": "desk", "ik_sign_pub": "old", "pq_refs": False},
        {"device": "phone", "ik_sign_pub": "sign", "pq_refs": True},
    ]
    assert directory(api) == snapshot
    assert api("GET", "/v1/devices?username=alice")[0] == full
    bundle, _ = api("POST", "/v1/bundles/fetch", {"recipient": "alice:phone"})
    assert (bundle["opk_pub"], bundle["pq_opk_pub"]) == ("first", "pq1")
    assert (bundle["opks_remaining"], bundle["pq_opks_remaining"]) == (1, 1)
    assert directory(api) == snapshot
    pk.update(spk_pub="rotated", opks=["refilled"], pq_opks=[], spk_signature="rotated-sig")
    register(api, "phone", identity_key="top", one_time_prekeys=["refilled"], public_keys=pk)
    assert directory(api) == snapshot


def test_version_tracks_each_long_term_field_and_active_device(request_api):
    api = request_api
    empty = directory(api)
    assert empty["devices"] == []
    assert empty["version"] != directory(api, "bobby")["version"]
    fields = {"identity_key": "top", "public_keys": {
        "ik_sign_pub": "sign", "ik_dh_pub": "dh", "pq_pub": "pq", "pq_refs": 1}}
    register(api, **fields)
    prior = directory(api)["version"]
    assert prior != empty["version"]
    for key in ("ik_sign_pub", "ik_dh_pub", "pq_pub", "pq_refs", "identity_key"):
        if key == "identity_key":
            fields[key] = "replacement"
        else:
            fields["public_keys"][key] = 0 if key == "pq_refs" else "replacement"
        register(api, **fields)
        current = directory(api)["version"]
        assert prior != current, key
        prior = current
    register(api, "desk")
    assert directory(api)["version"] != prior
    api("DELETE", "/v1/devices/alice/desk")
    assert directory(api)["version"] == prior


def test_guarded_send_validates_before_recipient_lookup_and_enqueue(request_api):
    api = request_api
    register(api)
    before = directory(api)["version"]
    register(api, "desk")
    body = {"sender": "bobby:desk", "recipient": "alice:phone", "ciphertext": "YQ=="}
    for recipient in ("alice:phone", "alice:unknown"):
        error, _ = api("POST", "/v1/envelopes", {**body, "recipient": recipient},
                       [("X-Directory-Version", before)], status=409)
        assert error["error"] == "DIRECTORY_CHANGED"
    current = directory(api)["version"]
    for values in ([""], ["*"], ["a" * 63], ["A" * 64], [current, current]):
        api("POST", "/v1/envelopes", body, [("X-Directory-Version", v) for v in values], status=400)
    api("POST", "/v1/directory/envelopes", body, status=400)
    error, _ = api("POST", "/v1/directory/envelopes", body,
                   [("X-Directory-Version", before)], status=409)
    assert error["error"] == "DIRECTORY_CHANGED"
    assert api("GET", "/v1/inbox/count?recipient=alice:phone")[0]["queued"] == 0
    api("POST", "/v1/envelopes", body, [("X-Directory-Version", current)], status=201)
    api("POST", "/v1/directory/envelopes", body, [("X-Directory-Version", current)], status=201)
    api("POST", "/v1/envelopes", {**body, "opaque_extension": 7}, status=201)
    legacy, headers = api("GET", "/v1/inbox?recipient=alice:phone")
    assert headers["Cache-Control"] == "no-store"
    assert set(legacy) == {"recipient", "delivered_count", "envelopes"}
    assert legacy["delivered_count"] == 3
    assert legacy["envelopes"][2]["opaque_extension"] == 7
    assert current not in json.dumps(legacy)
    _, cors = api("OPTIONS", "/v1/envelopes", status=204)
    assert "x-directory-version" in cors["Access-Control-Allow-Headers"].lower()
    api("DELETE", "/v1/devices/alice/phone")
    error, _ = api("POST", "/v1/envelopes", body, [("X-Directory-Version", current)], status=409)
    assert error["error"] == "DIRECTORY_CHANGED"
    api("POST", "/v1/envelopes", body, status=410)


def test_inbox_hint_is_opt_in_and_invalid_hint_preserves_mail(request_api):
    api = request_api
    register(api)
    version = directory(api, "bobby")["version"]
    path = "/v1/inbox?recipient=alice:phone"
    body = {"sender": "bobby:desk", "recipient": "alice:phone", "ciphertext": "Yg=="}
    api("POST", "/v1/envelopes", body, status=201)
    for bad in ("", "ab", "bobby%0A", "bobby&directory_user=alice"):
        api("GET", path + "&directory_user=" + bad, status=400)
    hint, _ = api("GET", path + "&directory_user=bobby")
    assert hint["directory_version"] == version
    assert hint["delivered_count"] == 1
    assert hint["envelopes"][0]["ciphertext"] == "Yg=="
    assert "directory_version" not in hint["envelopes"][0]
    assert api("GET", path + "&directory_user=bobby")[0]["directory_version"] == version
    assert "directory_version" not in api("GET", path)[0]
    for bad in ("", "alice%0A", "alice&username=bobby"):
        api("GET", "/v1/directory?username=" + bad, status=400)


def test_directory_version_survives_sqlite_reopen_and_registration_order(tmp_path):
    def seed(api, devices):
        for device in devices:
            register(api, device, identity_key=device + "-key")
        return directory(api)

    path = str(tmp_path / "relay.db")
    with serving(SQLiteStore(path)) as api:
        snapshot = seed(api, ["phone", "desk"])
    with serving(SQLiteStore(path)) as api:
        assert directory(api) == snapshot
    with serving(MemoryStore()) as api:
        assert seed(api, ["desk", "phone"]) == snapshot


def test_long_poll_reports_peer_version_at_delivery_and_online_status_is_excluded():
    entered_inbox = threading.Event()

    class ObservedMemoryStore(MemoryStore):
        def pop_all(self, username, device):
            entered_inbox.set()
            return super().pop_all(username, device)

    relay = Relay(ObservedMemoryStore())
    relay.register_device({"username": "alice", "device": "phone"})
    alice = relay.directory("alice")
    absent = relay.directory("bobby")["version"]
    with ThreadPoolExecutor(max_workers=1) as pool:
        inbox = pool.submit(relay.fetch_inbox, "alice", "phone", 5, "bobby")
        assert entered_inbox.wait(timeout=3)
        assert relay.list_devices("alice")["devices"][0]["online"] is True
        assert relay.directory("alice") == alice
        relay.register_device({"username": "bobby", "device": "desk"})
        relay.send_envelope({"sender": "bobby:desk", "recipient": "alice:phone", "ciphertext": "YQ=="})
        delivered = inbox.result(timeout=3)
    assert delivered["delivered_count"] == 1
    assert delivered["directory_version"] == relay.directory("bobby")["version"]
    assert delivered["directory_version"] != absent
