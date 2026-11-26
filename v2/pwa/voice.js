'use strict';
// send and receive operate at the authenticated, per-device ratchet boundary.
// The controller has no relay API, demo transport or cleartext signalling path.
(function (root) {
  const api = typeof module !== 'undefined' && module.exports
    ? require('./voice-signalling.js') : root.ECNUVoice;
  const {CallSession, INVITE_TIMEOUT_MS} = api;
  const address = /^[a-zA-Z0-9_.-]{3,20}:[a-zA-Z0-9_.-]{1,64}$/;
  const callId = /^call-[0-9a-f]{32}$/;

  function audioDescription(description, type) {
    if (!description || description.type !== type || typeof description.sdp !== 'string') return false;
    const media = description.sdp.split(/\r?\n/).filter(line => line.startsWith('m='));
    return media.length === 1 && media[0].startsWith('m=audio ');
  }

  function stopStream(stream) {
    if (stream) for (const track of stream.getTracks()) track.stop();
  }

  class VoiceController {
    constructor(options) {
      if (!options || typeof options.send !== 'function') throw Error('An encrypted device transport is required');
      this.send = options.send;
      this.onState = options.onState || (() => {});
      this.onRemoteStream = options.onRemoteStream || (() => {});
      this.nowMs = options.nowMs || Date.now;
      this.setTimer = options.setTimeout || root.setTimeout.bind(root);
      this.clearTimer = options.clearTimeout || root.clearTimeout.bind(root);
      this.createPeerConnection = options.createPeerConnection || (config => new root.RTCPeerConnection(config));
      this.getUserMedia = options.getUserMedia || (constraints => {
        if (!root.navigator?.mediaDevices?.getUserMedia) throw Error('Microphone access requires HTTPS or localhost');
        return root.navigator.mediaDevices.getUserMedia(constraints);
      });
      this.call = null;
      this.last = {state: 'idle', peer: null, role: null, callId: null, reason: null, muted: false, connectedAt: null};
      this.endedIds = new Map();
    }

    snapshot() {
      if (!this.call) return {...this.last};
      const {session, muted, connectedAt} = this.call;
      return {state: session.state, peer: session.peer, role: session.role, callId: session.callId,
        reason: session.endedReason, muted, connectedAt};
    }

    _begin(session) {
      const ctx = {session, muted: false, connectedAt: null, timer: null, pc: null,
        local: null, remoteTracks: new Set(), answering: false, announced: session.role === 'callee',
        localIce: [], remoteIce: [], canTrickle: false, remoteReady: false,
        sending: Promise.resolve(), addingIce: Promise.resolve()};
      this.call = ctx;
      this._setDeadline(ctx, session.createdAtMs + INVITE_TIMEOUT_MS - this.nowMs(), 'expired');
      this.onState(this.snapshot());
      return ctx;
    }

    _setDeadline(ctx, delay, reason) {
      this.clearTimer(ctx.timer);
      ctx.timer = this.setTimer(() => {
        if (this.call === ctx) this._abort(ctx, reason);
      }, Math.max(0, delay));
    }

    _send(ctx, signal, terminal = false) {
      const result = ctx.sending.then(() => {
        if (!terminal && this.call !== ctx) return;
        ctx.announced = true;
        return this.send(ctx.session.peer, signal);
      });
      // A terminal notification can follow a failed or still-pending offer.
      ctx.sending = result.catch(() => {});
      return result;
    }

    _finish(ctx, reason, signal) {
      if (this.call !== ctx) return Promise.resolve();
      ctx.session.state = 'ended';
      ctx.session.endedReason = reason;
      this.last = this.snapshot();
      this.call = null;
      this.clearTimer(ctx.timer);
      const pc = ctx.pc;
      if (pc) {
        pc.onicecandidate = pc.ontrack = pc.onconnectionstatechange = pc.oniceconnectionstatechange = null;
        pc.close();
      }
      stopStream(ctx.local);
      for (const track of ctx.remoteTracks) track.stop();
      this._rememberEnded(ctx.session.peer, ctx.session.callId);
      this.onRemoteStream(null);
      this.onState(this.snapshot());
      return signal && ctx.announced ? this._send(ctx, signal, true) : Promise.resolve();
    }

    _abort(ctx, reason) {
      const type = reason === 'expired' ? 'call-expired' : 'call-hangup';
      this._finish(ctx, reason, {type, call_id: ctx.session.callId}).catch(() => {});
    }

    _pruneIds() {
      const now = this.nowMs();
      for (const [key, end] of this.endedIds) if (end <= now) this.endedIds.delete(key);
    }

    _rememberEnded(peer, id) {
      this._pruneIds();
      this.endedIds.set(peer + '/' + id, this.nowMs() + INVITE_TIMEOUT_MS);
    }

    _sendIce(ctx, candidates) {
      const message = {type: 'call-ice', call_id: ctx.session.callId, ice_candidates: candidates};
      this._send(ctx, message).catch(() => this._abort(ctx, 'failed'));
    }

    async _openMedia(ctx) {
      const stream = await this.getUserMedia({audio: true});
      if (this.call !== ctx) { stopStream(stream); return false; }
      ctx.local = stream;
      const tracks = stream.getAudioTracks();
      if (!tracks.length) throw Error('Microphone returned no audio track');
      const pc = this.createPeerConnection({iceServers: []});
      ctx.pc = pc;
      pc.onicecandidate = event => {
        if (this.call !== ctx || !event.candidate) return;
        const candidate = event.candidate.toJSON();
        if (ctx.canTrickle) this._sendIce(ctx, [candidate]);
        else ctx.localIce.push(candidate);
      };
      pc.ontrack = event => {
        if (this.call !== ctx || event.track.kind !== 'audio') return;
        ctx.remoteTracks.add(event.track);
        this.onRemoteStream(event.streams[0] || new root.MediaStream([event.track]));
      };
      pc.onconnectionstatechange = pc.oniceconnectionstatechange = () => this._connectionChanged(ctx);
      for (const track of tracks) {
        track.enabled = !ctx.muted;
        pc.addTrack(track, stream);
      }
      return true;
    }

    _connectionChanged(ctx) {
      if (this.call !== ctx) return;
      const pc = ctx.pc;
      // The aggregate connection state includes DTLS. ICE alone proves
      // network reachability, so it cannot start the in-call timer.
      const state = pc.connectionState;
      if (state === 'failed' || state === 'closed' || pc.iceConnectionState === 'failed') {
        this._abort(ctx, 'failed');
        return;
      }
      if (state === 'disconnected' && ctx.session.state === 'in-call') {
        this._setDeadline(ctx, 10000, 'disconnected');
      }
      if (state !== 'connected') return;
      if (ctx.session.state === 'connecting') {
        ctx.session.markConnected();
        ctx.connectedAt = this.nowMs();
        this.onState(this.snapshot());
      }
      if (ctx.session.state === 'in-call') this.clearTimer(ctx.timer);
    }

    async _sendDescription(ctx, signal) {
      await this._send(ctx, signal);
      if (this.call !== ctx) return;
      ctx.canTrickle = true;
      if (ctx.localIce.length) this._sendIce(ctx, ctx.localIce.splice(0));
    }

    async _applyRemote(ctx, description) {
      await ctx.pc.setRemoteDescription(description);
      if (this.call !== ctx) return;
      ctx.remoteReady = true;
      await this._flushRemoteIce(ctx);
    }

    _flushRemoteIce(ctx) {
      if (!ctx.remoteReady || !ctx.remoteIce.length) return Promise.resolve();
      const candidates = ctx.remoteIce.splice(0);
      ctx.addingIce = ctx.addingIce.then(async () => {
        for (const candidate of candidates) {
          if (this.call !== ctx) return;
          await ctx.pc.addIceCandidate(candidate);
        }
      });
      return ctx.addingIce;
    }

    async start(peer) {
      if (typeof peer !== 'string' || !address.test(peer)) throw Error('Select a peer device');
      if (this.call) throw Error('Already in a call');
      const session = new CallSession('caller', peer, {nowMs: this.nowMs});
      const invite = session.invite();
      const ctx = this._begin(session);
      try {
        if (!await this._openMedia(ctx)) return;
        const offer = await ctx.pc.createOffer();
        if (this.call !== ctx) return;
        await ctx.pc.setLocalDescription(offer);
        if (this.call !== ctx) return;
        invite.sdp_offer = {type: offer.type, sdp: offer.sdp};
        invite.sent_at_ms = session.createdAtMs = this.nowMs();
        this._setDeadline(ctx, INVITE_TIMEOUT_MS, 'expired');
        await this._sendDescription(ctx, invite);
      } catch (error) {
        if (this.call !== ctx) return;
        this._abort(ctx, 'failed');
        throw error;
      }
    }

    async accept() {
      const ctx = this.call;
      if (!ctx || ctx.session.state !== 'ringing' || ctx.answering) return;
      if (ctx.session.isExpired()) { this._abort(ctx, 'expired'); return; }
      ctx.answering = true;
      try {
        if (!await this._openMedia(ctx)) return;
        await this._applyRemote(ctx, ctx.session.sdpOffer);
        if (this.call !== ctx) return;
        const answer = await ctx.pc.createAnswer();
        if (this.call !== ctx) return;
        await ctx.pc.setLocalDescription(answer);
        if (this.call !== ctx) return;
        const signal = ctx.session.accept({type: answer.type, sdp: answer.sdp});
        this._connecting(ctx);
        await this._sendDescription(ctx, signal);
      } catch (error) {
        if (this.call !== ctx) return;
        this._abort(ctx, ctx.session.endedReason || 'failed');
        throw error;
      }
    }

    _connecting(ctx) {
      this._setDeadline(ctx, INVITE_TIMEOUT_MS, 'failed');
      this.onState(this.snapshot());
      this._connectionChanged(ctx);
    }

    _receiveInvite(peer, message) {
      const now = this.nowMs();
      if (!Number.isSafeInteger(message.sent_at_ms) || message.sent_at_ms > now + INVITE_TIMEOUT_MS ||
          now - message.sent_at_ms >= INVITE_TIMEOUT_MS || !audioDescription(message.sdp_offer, 'offer')) return;
      this._pruneIds();
      if (this.endedIds.has(peer + '/' + message.call_id)) return;
      if (this.call) {
        const active = this.call.session;
        if (active.callId === message.call_id && active.peer === peer) return;
        this._rememberEnded(peer, message.call_id);
        return this.send(peer, {type: 'call-reject', reason: 'busy', call_id: message.call_id});
      }
      const session = new CallSession('callee', peer, {nowMs: this.nowMs});
      session.receiveInvite(message, now);
      const ctx = this._begin(session);
      ctx.remoteIce.push(...(message.ice_candidates || []));
    }

    async receive(peer, message) {
      if (typeof peer !== 'string' || !address.test(peer) || !message ||
          typeof message.call_id !== 'string' || !callId.test(message.call_id)) return;
      const candidates = message.ice_candidates;
      if (candidates !== undefined && (!Array.isArray(candidates) || candidates.length > 128 ||
          candidates.some(item => !item || typeof item.candidate !== 'string'))) return;
      if (message.type === 'call-invite') return this._receiveInvite(peer, message);
      const ctx = this.call;
      if (!ctx || ctx.session.peer !== peer || ctx.session.callId !== message.call_id) {
        // An authenticated cancellation can overtake a delayed invite.
        if (message.type === 'call-hangup' || message.type === 'call-expired') this._rememberEnded(peer, message.call_id);
        return;
      }
      const session = ctx.session;
      try {
        switch (message.type) {
          case 'call-accept':
            if (session.role !== 'caller' || session.state !== 'inviting' || !ctx.announced ||
                !audioDescription(message.sdp_answer, 'answer')) return;
            if (session.isExpired()) { this._abort(ctx, 'expired'); return; }
            session.receiveAccept(message);
            this._connecting(ctx);
            ctx.remoteIce.push(...(candidates || []));
            await this._applyRemote(ctx, session.sdpAnswer);
            break;
          case 'call-ice':
            if (!candidates || ctx.remoteIce.length + candidates.length > 128) return;
            ctx.remoteIce.push(...candidates);
            await this._flushRemoteIce(ctx);
            break;
          case 'call-reject':
            if (session.role !== 'caller' || session.state !== 'inviting') return;
            session.receiveReject(message);
            await this._finish(ctx, session.endedReason);
            break;
          case 'call-hangup':
            session.receiveHangup(message);
            await this._finish(ctx, session.endedReason);
            break;
          case 'call-expired':
            if (session.state === 'ringing' || session.state === 'inviting' || session.state === 'connecting')
              await this._finish(ctx, 'expired');
            break;
        }
      } catch (error) {
        if (this.call !== ctx) return;
        this._abort(ctx, 'failed');
        throw error;
      }
    }

    async decline() {
      const ctx = this.call;
      if (!ctx || ctx.session.state !== 'ringing') return;
      const signal = ctx.session.reject('declined');
      await this._finish(ctx, 'declined', signal);
    }

    async hangup() {
      const ctx = this.call;
      if (!ctx) return;
      const signal = ctx.session.hangup();
      await this._finish(ctx, 'hangup', signal);
    }

    setMuted(value) {
      const ctx = this.call;
      if (!ctx) return;
      ctx.muted = Boolean(value);
      if (ctx.local) for (const track of ctx.local.getAudioTracks()) track.enabled = !ctx.muted;
      this.onState(this.snapshot());
    }
  }

  api.VoiceController = VoiceController;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
