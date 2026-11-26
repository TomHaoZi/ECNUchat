# ECNUchat v2 — browser client

Plain HTML/CSS/JS. **No build step.** Open `index.html` in a browser,
or serve the folder (recommended, for SubtleCrypto + service worker):

```sh
cd v2/pwa
python -m http.server 8000 --bind 127.0.0.1
# then open http://127.0.0.1:8000/
# (the relay itself defaults to http://127.0.0.1:8765 — a different port)
```

In another terminal at the repository root, start the v2 relay with
`python v2/relay/relay.py`. For two local identities, open the PWA in
two browser profiles or open the second tab with `?profile=peer`.
Register both in relay mode and exchange their invites.

## Relay mode — real, classical, and tested against the real relay

Relay mode uses `crypto.js` (tweetnacl 1.0.3, vendored in `vendor/`,
plus WebCrypto AES-256-GCM) implementing the original Python v1's
classical design: X25519 X3DH (`x3dh-v1` HKDF, salt = 32 zero bytes),
double ratchet (`dr-v1` HKDF, HMAC 0x01/0x02 chain step, AAD =
sender || receiver || n || pn || dh_pub), per-message AES-256-GCM,
skipped-key cache (40), replay rejection, and ratchet payload fields
`dh_pub, n, pn, nonce, ciphertext, kind` plus `x3dh` on the first
message only. SK is never a message key.

It speaks **exactly** the real relay API in `../relay/README.md`:

- `POST /v1/devices/register` with
  `{username, device, identity_key, signed_prekey, one_time_prekeys, public_keys}`
  (public_keys carries the bundle `ik_sign_pub, ik_dh_pub, spk_pub,
  spk_signature, opk_pub`; the signed-prekey signature is verified
  by the peer before a session is accepted).
- `POST /v1/envelopes` with flat
  `{sender, recipient, ciphertext, protocol_version: "v1",
  message_type: "text", dh_pub, n, pn, nonce, kind, x3dh}`.
  `ciphertext` is base64 of the raw AES-GCM output (plaintext + tag).
- `GET /v1/inbox?recipient=username:device` — pop-on-fetch,
  **no ack endpoint** (a fetch already deletes; a client crash
  after fetching loses those envelopes — relay semantics, see
  `../relay/README.md`).
- `GET /v1/devices?username=<username>` supplies full public bundles for
  peer verification. The local cached client uses `GET /v1/directory`
  for fan-out and submits one guarded envelope per approved device.
- Default relay URL: `http://127.0.0.1:8765` (the relay default).
  The old defaults (`:8000`, `/v1/messages`, `/v1/inbox?username=&device_id=`,
  `/v1/messages/:id/ack`, `demo-1` envelopes) are gone from relay mode.

How to use relay mode:

1. Register a username: 3–20 chars, letters/digits/underscore only
   (same rule as v1). The browser generates a real identity
   (Ed25519 signing key, X25519 DH key, signed prekey, one one-time
   prekey) and a device id (`dev-…`). Your identity is
   `username:device`, shown with a SHA-256 fingerprint of the
   Ed25519 identity key (same rendering as v1: 16 groups of 4
   uppercase hex chars).
2. Copy your invite (JSON: username + device + relay URL +
   fingerprint) and paste it as a friend on another profile, or
   paste a friend's invite here. In relay mode the friend's
   devices are then fetched from the relay directory.
3. Pick the friend, type a message, then choose “Send to all devices”.
   The first message to a device carries the public session handshake.
4. “Fetch inbox now” (also polled every 5 seconds in relay mode)
   fetches, decrypts, and stores the session for each sender device.

### Cached contact devices on the local relay

The app saves a compact device list and its version in the browser profile.
For the active conversation, each inbox poll checks the version. Every chat
or call-signalling send using the cache carries the version. The relay checks
it while holding the same lock used to enqueue. A change forces a directory
refresh before sending to the remaining approved devices.

Exchange device invites through a trusted channel. Paste an additional invite
into **Add friend or verify device** to approve a new or replaced device. The
UI shows pending devices in the friend list. Peers already approved can keep
receiving messages. An observed removal withdraws local approval. The cache
contains public fingerprints, device IDs, capability flags and the version.
Starting a session still fetches and verifies the live prekey bundle.

This experiment uses the updated loopback relay. The benchmark uses
`?dircache=0` to reproduce the previous full-directory client.
[Local measurements and verification](../../docs/benchmarks/directory-cache.md)

### Local hybrid encapsulation experiment

Register both devices on a loopback relay to try compact hybrid messages.
The app advertises `pq_refs: 1` in the public device bundle. Until the
peer authenticates a full packet, saves its receiving state, and returns
a verifiable `pq_ack_v1` envelope, the sender repeats the full ML-KEM
encapsulation. During initial setup it also repeats the public PQXDH
handshake, so a later packet can bootstrap after an earlier one is lost.
After confirmation, each message on that sending chain can carry a
SHA-256 reference. Every new chain requires a fresh confirmation.

To reproduce the full-envelope baseline, open both profiles with
`?pqrefs=0` (or `?profile=peer&pqrefs=0`) and register fresh test
identities. Old peers use full hybrid envelopes. The local experiment
and its traffic measurements are documented in the
[benchmark report](../../docs/benchmarks/pq-reference.md).

### Voice calls

Both users keep the app open in relay mode. Under **Chat**, choose the
friend and their device, then select **Call**. The other device shows
the caller and can answer or decline. Allow microphone access when
calling or answering. During a call, either side can mute or hang up.
If the browser blocks autoplay, press play on the audio control.

SDP and ICE candidates travel inside one-to-one ratchet envelopes.
WebRTC carries audio directly between devices using DTLS-SRTP. This
build uses host ICE candidates only. Both devices need a direct path,
such as two profiles on the same PC. The local HTTP origin supports
microphone access on loopback. A remote browser needs a secure origin.

Run the two-profile browser test from the repository root with
`python -m pytest -s v2/tests/test_voice_browser.py`. It uses synthetic
audio, separate browser storage, and a temporary loopback relay.

## Demo mode — offline only, clearly separate, never sent to a relay

Demo mode keeps the old stand-in: the AES-256-GCM key is
`SHA-256(sorted(usernames) + ":DEMO-NOT-E2EE-REAL")`, every demo
message is tagged `DEMO-NOT-E2EE-REAL`, and demo envelopes travel
only over `BroadcastChannel` between tabs (or as a local simulated
reply). Demo traffic is effectively public. Demo mode never calls
the relay, and relay mode never sends a demo envelope.

## What is real vs stub

**Real in relay mode:**

- Username validation (v1 rule), local identity + device id,
  fingerprint display (SHA-256 of Ed25519 identity key).
- X25519 / Ed25519 via vendored tweetnacl; HKDF and AES-256-GCM
  via WebCrypto; X3DH + double ratchet as described above, with
  session persistence in localStorage (`sessionToJSON` /
  `sessionFromJSON` in `crypto.js`).
- Friend list, invite parsing (JSON or lines, now including an
  optional device line), per-device fan-out, message rendering,
  relay register / send / poll inbox per the real API.
- PWA manifest + service worker caching the **app shell only**
  (now including `crypto.js` and `vendor/nacl-fast.min.js`;
  never messages/keys/relay traffic).

- ML-KEM-768 / PQXDH / hybrid ratchet — **IMPLEMENTED in relay
  mode** (`crypto-pq.js`, vendored noble ML-KEM-768). A session is hybrid
  (`pqxdh-v1` / `pq-dr-v1`) iff both sides hold a PQ key; sessions
  with a no-PQ peer stay classical `x3dh-v1` / `dr-v1`, and a PQ
  peer refuses a classical initial (no silent downgrade).
- One-to-one voice calls in relay mode — see **Voice calls** above.

**Remaining PWA gaps**

- The app UI uses the v2 HTTP relay. The v1 desktop uses a different
  WebSocket transport for messaging and a different audio protocol.
- Groups (including Sender Keys / MLS) — absent.
- Push notifications (including wake-only Web Push) — absent.
- Encrypted backup / restore, device endorsement (scan-to-approve
  a new device) — absent. A revoke button is also absent in this
  client (revocation exists relay-side only; see relay README).
- Sealed sender is absent. The relay sees sender and recipient addresses.
  The local cached client checks signing-key fingerprints against the
  contact's device invites.
- WebSocket transport, TLS/WSS — absent from the local relay;
  production TLS must come from the deployment.

## Security warnings

- Treat demo traffic as public. Do not send real secrets through
  demo mode, and do not deploy this client over plain http for
  real use: production relays require TLS/WSS.
- Keys live in `localStorage` under a key starting `ecnu-chat-v2`
  (plus `-peer` for the peer tab). This is explicitly **not**
  production-grade secure storage (no hardware keystore, no OS
  keychain, readable by any script on this origin). An older demo
  store under `ecnu-chat-v2-demo` is NOT migrated; re-registering
  creates a new identity.
- The service worker caches only the app shell. It never caches
  messages, keys, or `/v1/` responses, and non-GET / cross-origin
  requests bypass it entirely.
- Clearing data: “Clear all DEMO data on this device” removes only
  this tab's namespace; repeat in the peer tab if you used one.
  (The button label is historical; it clears the current
  `ecnu-chat-v2` namespace, including real relay-mode identity.)
