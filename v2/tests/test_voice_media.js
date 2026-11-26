'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const api = require('../pwa/voice.js');

const PEER = 'alice:phone';
const ID = 'call-' + '1'.repeat(32);
const SDP = 'v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n';
const candidate = {candidate: 'candidate:1 1 UDP 1 127.0.0.1 17000 typ host', sdpMid: '0'};
function invite(sentAt = 100000, id = ID) {
  return {type: 'call-invite', call_id: id, sent_at_ms: sentAt,
    sdp_offer: {type: 'offer', sdp: SDP}, ice_candidates: []};
}
function audio() {
  const track = {kind: 'audio', enabled: true, stopped: false, stop() { this.stopped = true; }};
  return {track, getTracks: () => [track], getAudioTracks: () => [track]};
}
class FakePeer {
  constructor() { this.ice = []; this.connectionState = 'new'; }
  addTrack(track, stream) { this.outgoing = {track, stream}; }
  async createOffer() { return {type: 'offer', sdp: SDP}; }
  async createAnswer() { return {type: 'answer', sdp: SDP}; }
  async setLocalDescription(description) {
    this.localDescription = description;
    this.onicecandidate({candidate: {toJSON: () => candidate}});
  }
  async setRemoteDescription(description) { this.remoteDescription = description; }
  async addIceCandidate(value) {
    assert.ok(this.remoteDescription);
    this.ice.push(value);
  }
  connect() { this.connectionState = 'connected'; this.onconnectionstatechange(); }
  close() { this.closed = true; }
}
function setup(extra = {}) {
  const sent = [], media = [], pcs = [], states = [], remote = [], timers = new Map();
  let now = 100000, nextTimer = 0;
  const controller = new api.VoiceController({
    send: async (peer, message) => sent.push({peer, message}),
    onState: state => states.push(state), onRemoteStream: stream => remote.push(stream),
    nowMs: () => now,
    setTimeout: (fn, ms) => { const id = ++nextTimer; timers.set(id, {fn, at: now + ms}); return id; },
    clearTimeout: id => timers.delete(id),
    createPeerConnection: config => {
      assert.deepEqual(config.iceServers, []);
      const pc = new FakePeer(); pcs.push(pc); return pc;
    },
    getUserMedia: async constraints => {
      assert.deepEqual(constraints, {audio: true});
      const stream = audio(); media.push(stream); return stream;
    },
    ...extra
  });
  return {controller, sent, media, pcs, states, remote, timers,
    advance(ms) {
      now += ms;
      for (const [key, {fn, at}] of timers) if (at <= now) { timers.delete(key); fn(); }
    }};
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('caller sends its description before ICE and reports a call only after WebRTC connects', async () => {
  const h = setup();
  await h.controller.start(PEER);
  await settle();
  const [offer, ice] = h.sent.map(item => item.message);
  assert.ok(h.sent.every(item => item.peer === PEER));
  assert.equal(offer.type, 'call-invite');
  assert.equal(offer.sdp_offer.type, 'offer');
  assert.equal(offer.sent_at_ms, 100000);
  assert.match(offer.call_id, /^call-[a-f0-9]{32}$/);
  assert.equal(ice.type, 'call-ice');
  assert.equal(ice.call_id, offer.call_id);
  assert.equal(h.controller.snapshot().state, 'inviting');
  await h.controller.receive(PEER, {type: 'call-ice', call_id: offer.call_id, ice_candidates: [candidate]});
  await h.controller.receive(PEER, {type: 'call-accept', call_id: offer.call_id, sdp_answer: {type: 'answer', sdp: SDP}});
  assert.deepEqual(h.pcs[0].ice, [candidate]);
  assert.equal(h.controller.snapshot().state, 'connecting');
  h.advance(500);
  h.pcs[0].connect();
  assert.equal(h.controller.snapshot().state, 'in-call');
  assert.equal(h.controller.snapshot().connectedAt, 100500);
  h.controller.setMuted(true);
  assert.equal(h.pcs[0].outgoing.track.enabled, false);
  const incoming = audio();
  h.pcs[0].ontrack({track: incoming.track, streams: [incoming]});
  assert.equal(h.remote.at(-1), incoming);
  await h.controller.hangup();
  assert.equal(h.sent.at(-1).message.type, 'call-hangup');
  assert.equal(h.timers.size, 0);
  assert.equal(h.pcs[0].closed, true);
  assert.equal(h.media[0].track.stopped, true);
  assert.equal(incoming.track.stopped, true);
  assert.equal(h.remote.at(-1), null);
});

test('ringing accepts only signals for this peer device and call; reject and busy never open the microphone', async () => {
  const h = setup();
  await h.controller.receive(PEER, invite());
  await h.controller.receive(PEER, invite()); // repeated delivery is not a busy refusal
  assert.equal(h.controller.snapshot().state, 'ringing');
  assert.equal(h.sent.length, 0);
  await h.controller.receive('alice:laptop', {type: 'call-hangup', call_id: ID});
  await h.controller.receive(PEER, {type: 'call-hangup', call_id: 'call-' + '2'.repeat(32)});
  await h.controller.receive('bob:phone', invite(100000, 'call-' + '3'.repeat(32)));
  assert.equal(h.controller.snapshot().state, 'ringing');
  assert.equal(h.sent.at(-1).peer, 'bob:phone');
  assert.equal(h.sent.at(-1).message.reason, 'busy');
  await h.controller.decline();
  assert.equal(h.sent.at(-1).message.type, 'call-reject');
  assert.equal(h.controller.snapshot().state, 'ended');
  await h.controller.receive(PEER, invite());
  assert.equal(h.controller.snapshot().state, 'ended');
  assert.equal(h.media.length + h.pcs.length + h.timers.size, 0);
});

test('callee opens audio only on answer and applies candidates that arrived while ringing', async () => {
  const h = setup();
  await h.controller.receive(PEER, invite());
  await h.controller.receive(PEER, {type: 'call-ice', call_id: ID, ice_candidates: [candidate]});
  assert.equal(h.pcs.length + h.media.length, 0);
  await h.controller.accept();
  await settle();
  assert.deepEqual(h.sent.map(item => item.message.type), ['call-accept', 'call-ice']);
  assert.equal(h.sent[0].message.sdp_answer.type, 'answer');
  assert.equal(h.pcs[0].remoteDescription.type, 'offer');
  assert.deepEqual(h.pcs[0].ice, [candidate]);
  assert.equal(h.controller.snapshot().state, 'connecting');
  await h.controller.receive(PEER, {type: 'call-hangup', call_id: ID});
  assert.equal(h.controller.snapshot().reason, 'remote-hangup');
  assert.equal(h.pcs[0].closed && h.media[0].track.stopped, true);
  assert.equal(h.timers.size, 0);
});

test('stale, undated, invalid or non-audio invites never ring; a delayed live invite rings only until its original deadline', async () => {
  const h = setup();
  for (const bad of [invite(55000), {...invite(), sent_at_ms: null}, invite(100000, ''), {
    ...invite(), sdp_offer: {type: 'offer', sdp: SDP + 'm=video 9 UDP/TLS/RTP/SAVPF 96\r\n'}
  }]) await h.controller.receive(PEER, bad);
  await h.controller.receive('alice', invite());
  assert.equal(h.states.some(item => item.state === 'ringing'), false);
  await h.controller.receive(PEER, invite(56000));
  assert.equal(h.controller.snapshot().state, 'ringing');
  h.advance(1000);
  await settle();
  assert.equal(h.controller.snapshot().reason, 'expired');
  assert.equal(h.timers.size + h.media.length, 0);
});

test('hangup while microphone permission is pending releases a late stream and never disturbs the next call', async () => {
  let grant;
  const h = setup({getUserMedia: () => new Promise(resolve => { grant = resolve; })});
  await h.controller.receive(PEER, invite());
  const pending = h.controller.accept();
  await settle();
  await h.controller.receive(PEER, {type: 'call-hangup', call_id: ID});
  await h.controller.receive('bob:tablet', invite(100000, 'call-' + '4'.repeat(32)));
  const late = audio();
  grant(late);
  await pending;
  assert.equal(late.track.stopped, true);
  assert.equal(h.controller.snapshot().peer, 'bob:tablet');
  assert.equal(h.sent.length, 0);
  assert.ok(h.pcs.every(pc => pc.closed));
});

test('connection failure and failed invite delivery release hardware and expire setup timers', async () => {
  const h = setup({send: async () => { throw Error('relay offline'); }});
  await assert.rejects(h.controller.start(PEER), /relay offline/);
  assert.equal(h.controller.snapshot().state, 'ended');
  assert.equal(h.media[0].track.stopped && h.pcs[0].closed, true);
  assert.equal(h.timers.size, 0);
  const other = setup();
  await other.controller.receive(PEER, invite());
  await other.controller.accept();
  const pc = other.pcs[0];
  pc.connectionState = 'failed';
  pc.onconnectionstatechange();
  await settle();
  assert.equal(other.controller.snapshot().state, 'ended');
  assert.equal(other.media[0].track.stopped && pc.closed, true);
  assert.equal(other.timers.size, 0);
});

test('a cancellation delivered before its invite suppresses ringing only for the cancelling device', async () => {
  const h = setup();
  await h.controller.receive(PEER, {type: 'call-hangup', call_id: ID});
  await h.controller.receive(PEER, invite());
  assert.equal(h.controller.snapshot().state, 'idle');
  await h.controller.receive('alice:laptop', invite());
  assert.equal(h.controller.snapshot().state, 'ringing');
  assert.equal(h.controller.snapshot().peer, 'alice:laptop');
});

test('protocol fields must contain string IDs and addresses', async () => {
  const h = setup();
  await h.controller.receive([PEER], invite());
  await h.controller.receive(PEER, invite(100000, [ID]));
  assert.equal(h.controller.snapshot().state, 'idle');
  await assert.rejects(h.controller.start([PEER]));
  assert.equal(h.media.length + h.timers.size, 0);
});

test('a pending invite delivery cannot hold the microphone or send ICE after local hangup', async () => {
  const order = [];
  let deliver;
  const h = setup({send: async (_peer, message) => {
    order.push(message.type);
    if (message.type === 'call-invite') await new Promise(resolve => { deliver = resolve; });
  }});
  const dial = h.controller.start(PEER);
  await settle();
  const end = h.controller.hangup();
  assert.equal(h.media[0].track.stopped && h.pcs[0].closed, true);
  assert.equal(h.controller.snapshot().state, 'ended');
  deliver();
  await Promise.all([dial, end]);
  assert.deepEqual(order, ['call-invite', 'call-hangup']);
});

test('an ICE candidate pair alone does not report a connected audio call', async () => {
  const h = setup();
  await h.controller.receive(PEER, invite());
  await h.controller.accept();
  const pc = h.pcs[0];
  pc.connectionState = undefined;
  pc.iceConnectionState = 'connected';
  pc.oniceconnectionstatechange();
  assert.equal(h.controller.snapshot().state, 'connecting');
  pc.connect();
  assert.equal(h.controller.snapshot().state, 'in-call');
});
