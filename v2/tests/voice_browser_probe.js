// Installed before the app in each fresh test profile. Capture and RTP are native.
(() => {
  const peers = [];
  const tracks = [];
  let captureRequests = 0;
  const getUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
  navigator.mediaDevices.getUserMedia = async constraints => {
    captureRequests++;
    const stream = await getUserMedia(constraints);
    tracks.push(...stream.getTracks());
    return stream;
  };

  // Allow ICE checks only against the other local browser profile. Chromium's
  // allow-loopback-in-peer-connection switch adds loopback candidates.
  function loopbackCandidate(line) {
    return /^(?:127\.\d+\.\d+\.\d+|::1)$/.test(line.split(/\s+/)[4]);
  }
  window.RTCPeerConnection = class extends RTCPeerConnection {
    constructor(config, ...rest) {
      if (config?.iceServers?.length) throw new Error("This test requires host-only ICE");
      super(config, ...rest);
      peers.push(this);
    }
    setRemoteDescription(description) {
      const sdp = description.sdp.split("\r\n").filter(line =>
        !line.startsWith("a=candidate:") || loopbackCandidate(line)
      ).join("\r\n");
      return super.setRemoteDescription({ type: description.type, sdp });
    }
    addIceCandidate(candidate) {
      if (candidate?.candidate && !loopbackCandidate(candidate.candidate)) return Promise.resolve();
      return super.addIceCandidate(candidate);
    }
  };
  window.mediaProbe = {
    peers, tracks,
    get captureRequests() { return captureRequests; },
    async audio() {
      const pc = peers.find(connection => connection.connectionState === "connected");
      if (!pc) return null;
      const stats = Array.from((await pc.getStats()).values());
      const rtp = stats.find(s => s.type === "inbound-rtp" && s.kind === "audio");
      const transport = stats.find(s => s.type === "transport" && s.selectedCandidatePairId);
      const pair = stats.find(s => s.id === transport?.selectedCandidatePairId);
      if (!rtp || !pair) return null;
      return {
        packets: rtp.packetsReceived, bytes: rtp.bytesReceived, samples: rtp.totalSamplesReceived,
        local: stats.find(s => s.id === pair.localCandidateId)?.address,
        remote: stats.find(s => s.id === pair.remoteCandidateId)?.address,
        dtls: transport.dtlsState,
      };
    },
    released() {
      return peers.length && peers.every(pc => pc.connectionState === "closed") &&
        tracks.length && tracks.every(track => track.readyState === "ended") &&
        !document.querySelector("#voice-audio").srcObject;
    },
  };
})();
