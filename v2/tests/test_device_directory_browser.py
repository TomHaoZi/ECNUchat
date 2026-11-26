"""Exercise directory changes through real chat forms, Chromium profiles and a loopback relay."""

import json
from contextlib import ExitStack
from dataclasses import dataclass

import pytest

from v2.relay.relay import ApiError, Handler, MemoryStore, Relay
from v2.tests.test_pq_reference_browser import browser_and_assets, message, reload_page, send_from_chat
from v2.tests.test_voice_browser import Page, serve


DIRECTORY = "/v1/directory"
DEVICES = "/v1/devices"
GUARDED = "/v1/directory/envelopes"
ENVELOPES = "/v1/envelopes"
MANUAL_INBOX = """
    const nativeInterval = window.setInterval.bind(window);
    window.setInterval = (callback, delay, ...args) =>
        delay === 5000 ? 0 : nativeInterval(callback, delay, ...args);
    window.manualInbox = true;
"""


@dataclass
class Post:
    path: str
    recipient: str
    version: str | None
    status: int
    error: str | None
    initial: bool


class Chat:
    def __init__(self, clients, stack):
        self.cdp, self.pwa = clients
        self.stack = stack
        self.relay = Relay(MemoryStore())
        self.gets = []
        self.posts = []
        self.directory_unavailable = False
        self.after_first_accept = None
        chat = self

        class Capture(Handler):
            relay = chat.relay

            def _route(self, method):
                path = self.path.partition("?")[0]
                if method == "GET":
                    chat.gets.append(path)
                    if path == DIRECTORY and chat.directory_unavailable:
                        raise ApiError(503, "UNAVAILABLE", "Directory temporarily unavailable")
                return super()._route(method)

            def _read_json(self):
                self.body = super()._read_json()
                return self.body

            def _send_json(self, status, obj):
                if self.path in (ENVELOPES, GUARDED) and self.body.get("message_type") == "text":
                    post = Post(self.path, self.body["recipient"], self.headers.get("X-Directory-Version"),
                                status, obj.get("error"), bool(self.body.get("x3dh")))
                    chat.posts.append(post)
                    if status == 201 and chat.after_first_accept:
                        callback, chat.after_first_accept = chat.after_first_accept, None
                        callback(post.recipient)
                return super()._send_json(status, obj)

        self.url = stack.enter_context(serve(Capture))

    def profile(self, username, *, automatic=False, legacy=False, device=None):
        page = Page(self.cdp, self.pwa + ("/?dircache=0" if legacy else "/"),
                    preload="window.testAlerts = []; window.alert = m => testAlerts.push(m);"
                            + ("" if automatic else MANUAL_INBOX))
        context = page.command("Target.getTargetInfo", {})["targetInfo"]["browserContextId"]
        self.stack.callback(self.cdp.command, "Target.disposeBrowserContext", {"browserContextId": context})
        if device:
            # Model a reinstalled profile retaining the same address but generating fresh real keys.
            page.js(f"randomDeviceId = () => {json.dumps(device)}")
        return page, page.register(username, self.url)

    def establish(self, *, automatic=False, legacy=False):
        alice, _ = self.profile("alice", automatic=automatic, legacy=legacy)
        bob, invite = self.profile("bobby")
        add_verified(alice, invite)
        send_chat(alice, 0)
        receive(bob, [0])
        alice.js("fetchInbox()")
        self.gets.clear()
        self.posts.clear()
        return alice, bob, invite


@pytest.fixture(scope="module")
def clients():
    with browser_and_assets() as setup:
        yield setup


@pytest.fixture
def chat(clients):
    with ExitStack() as stack:
        yield Chat(clients, stack)


def visible(page, selector):
    return page.js(f"document.querySelector({json.dumps(selector)}).textContent")


def add_verified(page, invite):
    page.add_friend(invite)
    page.wait("Array.from(document.querySelector('#chat-friend').options)"
              f".some(o => o.value === {json.dumps(invite['username'])})", "contact in chat selector")
    page.fill("#chat-friend", invite["username"])
    device = json.dumps(invite["device"])
    page.wait(f"(!document.querySelector('#invite').value && "
              f"document.querySelector('#fanout').textContent.includes({device})) || testAlerts.length",
              "verified device in fan-out")
    assert invite["device"] in visible(page, "#fanout"), page.js("testAlerts")


def send_chat(page, index):
    send_from_chat(page, index)
    page.wait("!document.querySelector('#message-text').value || testAlerts.length", "fan-out completed")
    assert not page.js("testAlerts"), page.js("testAlerts")


def failed_send(page, index):
    page.js("testAlerts.length = 0")
    page.fill("#message-text", message(index))
    page.click("#send-form button")
    page.wait("testAlerts.length || !document.querySelector('#message-text').value", "send result")
    assert any("Send failed" in error for error in page.js("testAlerts"))
    assert page.js("document.querySelector('#message-text').value") == message(index)
    page.js("testAlerts.length = 0")


def receive(page, indices):
    page.js("fetchInbox()")
    assert page.js("state.messages.filter(m => m.dir === 'in').map(m => m.text)") == [
        message(i) for i in indices
    ]


def test_established_form_reuses_directory_after_reload(chat):
    alice, bob, _ = chat.establish()
    reload_page(alice)
    alice.fill("#chat-friend", "bobby")
    send_chat(alice, 1)
    send_chat(alice, 2)
    assert DIRECTORY not in chat.gets and DEVICES not in chat.gets, chat.gets
    assert len(chat.posts) == 2
    assert all(p.path == GUARDED and p.status == 201 and p.version for p in chat.posts)
    assert chat.posts[0].version == chat.posts[1].version
    receive(bob, [0, 1, 2])


def test_opt_out_uses_full_device_list_for_each_established_send(chat):
    alice, bob, _ = chat.establish(legacy=True)
    send_chat(alice, 1)
    send_chat(alice, 2)
    assert chat.gets.count(DEVICES) == 2 and DIRECTORY not in chat.gets
    assert [(p.path, p.version, p.status) for p in chat.posts] == [(ENVELOPES, None, 201)] * 2
    receive(bob, [0, 1, 2])


def test_added_device_requires_its_own_invite_before_next_delivery(chat):
    alice, bob, first = chat.establish()
    tablet, second = chat.profile("bobby")
    send_chat(alice, 1)  # First action since registration; the inbox timer is disabled.
    assert [(p.status, p.error) for p in chat.posts] == [(409, "DIRECTORY_CHANGED"), (201, None)]
    assert chat.posts[0].version and chat.posts[0].version != chat.posts[1].version
    assert chat.posts[1].recipient == "bobby:" + first["device"]
    assert second["device"] in visible(alice, "#friend-list")
    assert second["device"] not in visible(alice, "#fanout")
    receive(bob, [0, 1])
    receive(tablet, [])

    add_verified(alice, second)
    send_chat(alice, 2)
    receive(bob, [0, 1, 2])
    receive(tablet, [2])


def test_idle_selected_friend_reflects_addition_and_revocation_on_inbox_timer(chat):
    alice, _, first = chat.establish(automatic=True)
    _, second = chat.profile("bobby")
    chat.relay.revoke_device("bobby", first["device"])
    alice.wait(f"document.querySelector('#friend-list').textContent.includes({json.dumps(second['device'])})",
               "automatic inbox poll to discover replacement device", timeout=13)
    assert first["device"] not in visible(alice, "#friend-list")
    assert first["device"] not in visible(alice, "#fanout")
    assert second["device"] not in visible(alice, "#fanout")
    assert "/v1/inbox" in chat.gets and DIRECTORY in chat.gets
    assert not chat.posts


def test_revocation_between_fanout_posts_never_requeues_first_delivery(chat):
    alice, bob, first = chat.establish()
    tablet, second = chat.profile("bobby")
    phone, third = chat.profile("bobby")
    alice.js("fetchInbox()")
    add_verified(alice, second)
    add_verified(alice, third)
    send_chat(alice, 1)
    receive(bob, [0, 1])
    receive(tablet, [1])
    receive(phone, [1])
    chat.posts.clear()
    peers = {first["device"]: (bob, [0, 1, 2]), second["device"]: (tablet, [1, 2]),
             third["device"]: (phone, [1, 2])}
    revoked = None

    def revoke_remaining(accepted):
        nonlocal revoked
        revoked = next(d for d in peers if d != accepted.split(":")[1])
        chat.relay.revoke_device("bobby", revoked)

    chat.after_first_accept = revoke_remaining
    send_chat(alice, 2)
    assert [(p.status, p.error) for p in chat.posts] == [(201, None), (409, "DIRECTORY_CHANGED"), (201, None)]
    survivors = peers.keys() - {revoked}
    assert {p.recipient.split(":")[1] for p in chat.posts if p.status == 201} == survivors
    assert chat.relay.store.count("bobby", revoked) == 0
    assert revoked not in visible(alice, "#fanout")
    for device in survivors:
        receive(*peers[device])


def test_directory_unavailable_after_conflict_keeps_draft_and_enqueues_nothing(chat):
    alice, bob, _ = chat.establish()
    tablet, _ = chat.profile("bobby")
    chat.directory_unavailable = True
    failed_send(alice, 1)
    assert [(p.status, p.error) for p in chat.posts] == [(409, "DIRECTORY_CHANGED")]
    assert DIRECTORY in chat.gets and DEVICES not in chat.gets
    assert not alice.js(f"state.messages.some(m => m.text === {json.dumps(message(1))})")
    receive(bob, [0])
    receive(tablet, [])
    chat.directory_unavailable = False
    send_chat(alice, 1)
    receive(bob, [0, 1])
    receive(tablet, [])


def test_replaced_identity_at_same_device_requires_matching_invite_and_new_session(chat):
    alice, _, old = chat.establish()
    replacement, new = chat.profile("bobby", device=old["device"])
    assert old["fingerprint"] != new["fingerprint"]
    failed_send(alice, 1)
    assert [(p.status, p.error) for p in chat.posts] == [(409, "DIRECTORY_CHANGED")]
    assert old["device"] not in visible(alice, "#fanout")
    receive(replacement, [])

    alice.add_friend(old)
    alice.wait("testAlerts.some(m => m.includes('verification failed'))", "outdated invite rejected")
    failed_send(alice, 2)
    receive(replacement, [])
    add_verified(alice, new)
    send_chat(alice, 3)
    receive(replacement, [3])


def reload_pre_directory_session(alice, invite):
    address = json.dumps(invite["username"] + ":" + invite["device"])
    alice.js(f"""(() => {{
        const saved = JSON.parse(localStorage.getItem(STORE_KEY));
        const [key] = Object.keys(saved.sessions);
        const record = saved.sessions[key];
        if (record.mode !== 'hybrid' || !record.peerFingerprint) throw Error('Expected verified hybrid session');
        delete record.peerFingerprint;
        delete saved.sessions[key];
        saved.sessions[{address}] = record;
        localStorage.setItem(STORE_KEY, JSON.stringify(saved));
    }})()""")
    reload_page(alice)
    alice.fill("#chat-friend", invite["username"])


def test_old_hybrid_session_resumes_after_one_nonconsuming_signed_key_lookup(chat):
    alice, bob, invite = chat.establish()
    before = chat.relay.list_devices("bobby")["devices"][0]["public_keys"]
    initial_pools = (len(before["opks"]), len(before["pq_opks"]))
    reload_pre_directory_session(alice, invite)
    send_chat(alice, 1)
    send_chat(alice, 2)
    assert chat.gets.count(DEVICES) == 1
    assert [(p.status, p.initial) for p in chat.posts] == [(201, False), (201, False)]
    after = chat.relay.list_devices("bobby")["devices"][0]["public_keys"]
    assert (len(after["opks"]), len(after["pq_opks"])) == initial_pools
    receive(bob, [0, 1, 2])


def test_old_hybrid_session_cannot_be_adopted_under_a_replaced_identity(chat):
    alice, _, old = chat.establish()
    reload_pre_directory_session(alice, old)
    replacement, new = chat.profile("bobby", device=old["device"])
    failed_send(alice, 1)
    assert not any(p.status == 201 for p in chat.posts)
    receive(replacement, [])
    add_verified(alice, new)
    send_chat(alice, 2)
    assert chat.posts[-1].initial
    receive(replacement, [2])


@pytest.mark.parametrize("migrate", [True, False], ids=["old-record", "current-record"])
def test_hybrid_session_restarts_when_same_signer_publishes_a_new_kem_key(chat, migrate):
    alice, bob, invite = chat.establish()
    if migrate:
        reload_pre_directory_session(alice, invite)
    old = chat.relay.list_devices("bobby")["devices"][0]["public_keys"]
    # Model recovery from a backup that retained the Ed25519 identity but lost the KEM and ratchets.
    bob.js("""(async () => {
        delete state.profile.pq;
        state.sessions = {};
        await registerDeviceWithRelay();
    })()""")
    new = chat.relay.list_devices("bobby")["devices"][0]["public_keys"]
    assert old["ik_sign_pub"] == new["ik_sign_pub"] and old["pq_pub"] != new["pq_pub"]
    alice.js("fetchInbox()")
    chat.gets.clear()
    send_chat(alice, 1)
    assert [(p.status, p.initial) for p in chat.posts] == [(201, True)]
    assert chat.gets.count(DEVICES) == 1
    receive(bob, [0, 1])


def test_directory_change_cannot_downgrade_an_established_hybrid_peer(chat):
    alice, bob, invite = chat.establish()
    original, = chat.relay.list_devices("bobby")["devices"]
    classical_keys = {name: value for name, value in original["public_keys"].items()
                      if not name.startswith("pq_")}
    chat.relay.register_device({**original, "public_keys": classical_keys})
    alice.js("fetchInbox()")
    failed_send(alice, 1)
    assert not chat.posts
    assert chat.relay.store.count("bobby", invite["device"]) == 0
    chat.relay.register_device(original)
    alice.js("fetchInbox()")
    send_chat(alice, 2)
    assert [(post.status, post.initial) for post in chat.posts] == [(201, False)]
    receive(bob, [0, 2])


def test_identical_directory_on_another_relay_requires_new_approval_and_session(clients, chat):
    alice, bob, invite = chat.establish()
    with ExitStack() as stack:
        other = Chat(clients, stack)
        for username in ("alice", "bobby"):
            (record,) = chat.relay.list_devices(username)["devices"]
            other.relay.register_device(record)
        assert other.relay.directory("bobby")["version"] == chat.relay.directory("bobby")["version"]
        alice.fill("#relay-url", other.url)
        failed_send(alice, 1)
        assert DIRECTORY in other.gets and not other.posts
        assert other.relay.store.count("bobby", invite["device"]) == 0

        bob.fill("#relay-url", other.url)
        add_verified(alice, {**invite, "relay": other.url})
        send_chat(alice, 2)
        assert len(other.posts) == 1 and other.posts[0].initial
        receive(bob, [0, 2])
