'use strict';
/*
 * ECNUchat v2 — Track C (c): 1-to-1 voice signalling state machine.
 * Pure signalling states. The companion voice.js drives browser audio
 * and calls markConnected() after the peer connection reports connected.
 *
 * Signalling messages produced/consumed by this module are plain
 * objects that MUST be carried inside already-encrypted 1-to-1
 * double-ratchet envelopes (pwa/crypto.js sessionEncrypt), exactly
 * as docs/voice-webrtc.md §2 requires. The relay then sees only
 * ciphertext envelopes, never SDP, ICE candidates, or call content.
 * This module never encrypts anything itself and never sends
 * anything to a network; the caller transports the messages.
 *
 * States (per design doc §3): idle -> inviting / ringing ->
 * connecting -> in-call -> ended. One live call per client.
 * Invite expiry: ~45 seconds (INVITE_TIMEOUT_MS = 45000), enforced
 * by both sides' local timers (injectable `nowMs` for tests), not
 * by the relay. A late accept for an expired call id is rejected
 * and must not resurrect the call. A reject is final for that call
 * id; retry requires a new call id.
 */
(function (root) {
  var INVITE_TIMEOUT_MS = 45000;
  var STATES = ['idle', 'inviting', 'ringing', 'connecting', 'in-call', 'ended'];

  function randomCallId() {
    var b;
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      b = new Uint8Array(16); crypto.getRandomValues(b);
    } else if (typeof require === 'function') {
      b = new Uint8Array(require('crypto').randomBytes(16));
    } else throw new Error('No secure RNG available');
    var hex = ''; b.forEach(function (x) { hex += ('0' + x.toString(16)).slice(-2); });
    return 'call-' + hex;
  }

  function CallSession(role, peer, opts) {
    opts = opts || {};
    if (role !== 'caller' && role !== 'callee') throw new Error('role must be caller or callee');
    this.role = role; this.peer = peer;
    this.callId = opts.callId || null;
    this.state = 'idle';
    this.nowMs = opts.nowMs || function () { return Date.now(); };
    this.createdAtMs = null; this.endedReason = null;
    this.sdpOffer = null; this.sdpAnswer = null;
    this.iceCandidates = [];
  }
  CallSession.prototype.isLive = function () {
    return this.state !== 'idle' && this.state !== 'ended';
  };
  CallSession.prototype.isExpired = function (now) {
    if (this.createdAtMs === null) return false;
    return (now === undefined ? this.nowMs() : now) - this.createdAtMs >= INVITE_TIMEOUT_MS;
  };
  // Caller starts a call. Returns the invite message to carry in a
  // 1-to-1 ratchet envelope. sdpOffer / iceCandidates are opaque
  // signalling blobs supplied by the caller's WebRTC stack.
  CallSession.prototype.invite = function (sdpOffer, iceCandidates) {
    if (this.role !== 'caller') throw new Error('Only the caller can invite');
    if (this.state !== 'idle') throw new Error('Already in a call; one live call per client');
    this.callId = randomCallId();
    this.createdAtMs = this.nowMs();
    this.state = 'inviting';
    this.sdpOffer = sdpOffer || null;
    this.iceCandidates = iceCandidates || [];
    return { type: 'call-invite', call_id: this.callId, from: 'caller', sent_at_ms: this.createdAtMs,
      sdp_offer: this.sdpOffer, ice_candidates: this.iceCandidates };
  };
  // Callee receives an invite. If this client is already in a live
  // call, returns a busy reject WITHOUT disturbing the live call.
  // Otherwise moves to ringing and returns null (caller must wait
  // for accept/reject). `msg` must already have been decrypted and
  // authenticated by the 1-to-1 session; this module does not verify.
  CallSession.prototype.receiveInvite = function (msg, now) {
    if (this.role !== 'callee') throw new Error('Only the callee receives invites');
    if (this.isLive()) {
      return { type: 'call-reject', call_id: msg.call_id, reason: 'busy' };
    }
    if (this.state !== 'idle') throw new Error('Callee not idle');
    now = now === undefined ? this.nowMs() : now;
    this.callId = msg.call_id;
    this.createdAtMs = Number.isSafeInteger(msg.sent_at_ms) ? Math.min(msg.sent_at_ms, now) : now;
    this.sdpOffer = msg.sdp_offer || null;
    this.iceCandidates = msg.ice_candidates || [];
    this.state = 'ringing';
    return this.checkExpiry(now);
  };
  CallSession.prototype.accept = function (sdpAnswer, iceCandidates, now) {
    if (this.role !== 'callee') throw new Error('Only the callee accepts');
    if (this.state !== 'ringing') throw new Error('Cannot accept: not ringing');
    if (this.isExpired(now)) {
      this.state = 'ended'; this.endedReason = 'expired';
      throw new Error('Invite expired (~45s): late accept rejected, call id invalid');
    }
    this.state = 'connecting';
    this.sdpAnswer = sdpAnswer || null;
    this.iceCandidates = iceCandidates || [];
    return { type: 'call-accept', call_id: this.callId,
      sdp_answer: this.sdpAnswer, ice_candidates: this.iceCandidates };
  };
  CallSession.prototype.reject = function (reason) {
    if (this.state !== 'ringing' && this.state !== 'inviting') throw new Error('Cannot reject: no pending call');
    this.state = 'ended'; this.endedReason = reason || 'rejected';
    return { type: 'call-reject', call_id: this.callId, reason: this.endedReason };
  };
  CallSession.prototype.hangup = function () {
    if (!this.isLive()) throw new Error('Cannot hang up: no live call');
    var id = this.callId;
    this.state = 'ended'; this.endedReason = 'hangup';
    return { type: 'call-hangup', call_id: id };
  };
  // Caller receives the callee's accept. A late accept for an
  // expired invite is rejected here too (both sides enforce expiry).
  CallSession.prototype.receiveAccept = function (msg, now) {
    if (this.role !== 'caller') throw new Error('Only the caller receives accepts');
    if (this.state !== 'inviting') throw new Error('Cannot accept: not inviting');
    if (msg.call_id !== this.callId) throw new Error('Accept call_id mismatch');
    if (this.isExpired(now)) {
      this.state = 'ended'; this.endedReason = 'expired';
      throw new Error('Invite expired (~45s): late accept rejected');
    }
    this.state = 'connecting';
    this.sdpAnswer = msg.sdp_answer || null;
    this.iceCandidates = msg.ice_candidates || [];
    return true;
  };
  CallSession.prototype.receiveReject = function (msg) {
    if (msg.call_id !== this.callId) throw new Error('Reject call_id mismatch');
    if (!this.isLive()) throw new Error('Cannot reject: no live call');
    this.state = 'ended'; this.endedReason = msg.reason || 'rejected';
    return true;
  };
  CallSession.prototype.receiveHangup = function (msg) {
    if (msg.call_id !== this.callId) throw new Error('Hangup call_id mismatch');
    if (!this.isLive()) return false; // already ended: hangup is idempotent
    this.state = 'ended'; this.endedReason = 'remote-hangup';
    return true;
  };
  CallSession.prototype.receiveIce = function (msg) {
    if (msg.call_id !== this.callId) throw new Error('ICE call_id mismatch');
    if (!this.isLive()) throw new Error('ICE for non-live call');
    if (msg.ice_candidates) this.iceCandidates = this.iceCandidates.concat(msg.ice_candidates);
    return { type: 'call-ice', call_id: this.callId, ice_candidates: msg.ice_candidates || [] };
  };
  CallSession.prototype.markConnected = function () {
    if (this.state !== 'connecting') throw new Error('Media connects only from connecting state');
    this.state = 'in-call';
  };
  // Local expiry check the caller runs on its ringing timer.
  CallSession.prototype.checkExpiry = function (now) {
    if (this.isLive() && (this.state === 'inviting' || this.state === 'ringing') && this.isExpired(now)) {
      this.state = 'ended'; this.endedReason = 'expired';
      return { type: 'call-expired', call_id: this.callId };
    }
    return null;
  };

  var api = { INVITE_TIMEOUT_MS: INVITE_TIMEOUT_MS, STATES: STATES, CallSession: CallSession, randomCallId: randomCallId };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.ECNUVoice = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
