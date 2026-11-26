# One-to-one voice calls

The PWA uses the browser microphone and an `RTCPeerConnection` for live audio. The caller selects one friend device. The recipient can answer or decline before the browser requests microphone access. A call invite carries its creation time and expires after 45 seconds, including time spent in the relay inbox.

Offer, answer, trickle ICE and call-control messages travel through the same authenticated ratchet transport as one-to-one chat. The browser protects the media with DTLS-SRTP. The peer connection uses host ICE candidates with an empty ICE-server list. Both devices need a direct network path, and microphone access requires a secure context such as localhost or HTTPS.

## Client integration

Load `voice-signalling.js` followed by `voice.js` from the PWA root. CommonJS consumers can require `v2/pwa/voice.js` for the live controller. The earlier standalone signalling simulation remains available at `v2/voice/signalling.js`.

```js
const calls = new ECNUVoice.VoiceController({
  send: sendEncryptedSignalToDevice,
  onState: renderCallControls,
  onRemoteStream: stream => { audioElement.srcObject = stream; }
});
```

- `start(peerAddress)` dials one `username:device` address. `accept()`, `decline()` and `hangup()` act on the current call.
- Pass each decrypted signal and its authenticated sender address to `receive(peerAddress, signal)`. The sender and receiver callbacks operate on the complete device address.
- `setMuted(true)` disables the local audio track. `snapshot()` includes the call state, peer, role, call ID, mute state, connection time and end reason.
- `onRemoteStream` receives a browser media stream for playback, then `null` when the call ends. Ending a call closes the peer connection, stops the media tracks and clears the active timer.

Run `node --test v2/tests/test_voice_media.js` from the repository root for the controller tests with simulated microphones, peer connections and clocks.
