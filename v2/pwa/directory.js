'use strict';

// The compact directory is routing metadata. Trust comes from the device's
// signing-key fingerprint in an invite obtained from the contact.
function directoryCacheEnabled() {
  return params.get('dircache') !== '0' && isLocalRelay();
}
function directoryScope() {
  return JSON.stringify([relayBase(), meAddress(), state.profile.fingerprint]);
}
function assertLocalScope(scope) {
  if (!state.profile || state.mode !== 'relay' || directoryScope() !== scope) {
    throw new Error('Local identity or relay changed during this operation.');
  }
}
function cachedDirectory(friend) {
  return state.profile && friend.directory?.scope === directoryScope() ? friend.directory : null;
}
function routableDevices(friend) {
  if (!friend || (state.mode === 'relay' && directoryCacheEnabled() && !cachedDirectory(friend))) return [];
  return friend.devices || [];
}
function inviteFingerprint(value) {
  const hex = String(value || '').replace(/\s/g, '').toUpperCase();
  return /^[A-F0-9]{64}$/.test(hex) ? hex.match(/.{4}/g).join(' ') : null;
}
function trustedEntry(friend, entry) {
  return !!entry.fingerprint && friend.pinScope === directoryScope() &&
    friend.pins?.some(pin => pin.device === entry.device && pin.fingerprint === entry.fingerprint);
}
function assertDirectoryScope(friend, directory) {
  assertLocalScope(directory.scope);
  if (!state.friends.includes(friend)) throw new Error('Contact was removed during this operation.');
}
async function readFriendDirectory(friend, invite) {
  const scope = directoryScope();
  const base = relayBase();
  const data = await relayJson('/v1/directory?username=' + encodeURIComponent(friend.username),
    {cache: 'no-store'}, base);
  if (data?.username !== friend.username || typeof data.version !== 'string' || !/^[0-9a-f]{64}$/.test(data.version) ||
      !Array.isArray(data.devices)) throw new Error('Invalid device directory.');
  const ids = new Set();
  const entries = [];
  for (const row of data.devices) {
    if (typeof row?.device !== 'string' || !/^[a-zA-Z0-9_.-]{1,64}$/.test(row.device) ||
        ids.has(row.device) || typeof row.pq_refs !== 'boolean') throw new Error('Invalid device directory entry.');
    ids.add(row.device);
    let fingerprint = null;
    if (typeof row.ik_sign_pub === 'string' && /^[A-Za-z0-9+/]{43}=$/.test(row.ik_sign_pub)) {
      const key = unb64(row.ik_sign_pub);
      if (b64(key) === row.ik_sign_pub) fingerprint = await ECNUcrypto.fingerprintOf(key);
    }
    entries.push({device: row.device, fingerprint, pq_refs: row.pq_refs});
  }
  const directory = {scope, version: data.version, entries};
  assertDirectoryScope(friend, directory);
  const oldPins = friend.pinScope === scope ? friend.pins || [] : [];
  // Observed removal or key replacement withdraws approval. Reappearance
  // requires the matching invite again, even if the device ID is reused.
  const pins = oldPins.filter(pin =>
    entries.some(row => row.device === pin.device && row.fingerprint === pin.fingerprint));
  const firstInvite = !friend.pinScope && (!friend.relay || friend.relay.replace(/\/+$/, '') === base);
  const requested = invite || (firstInvite ? friend : null);
  let approved = false;
  if (requested) {
    const fingerprint = inviteFingerprint(requested.fingerprint);
    const matches = entries.filter(row => fingerprint && row.fingerprint === fingerprint &&
      (!requested.device || row.device === requested.device));
    if (matches.length === 1 && (!requested.relay || requested.relay.replace(/\/+$/, '') === base)) {
      const device = matches[0].device;
      if (!pins.some(p => p.device === device)) pins.push({device, fingerprint});
      approved = true;
    }
  }
  friend.pinScope = scope;
  friend.pins = pins;
  friend.directory = directory;
  friend.devices = entries.filter(row => trustedEntry(friend, row)).map(row => row.device);
  try { persist(); }
  catch (error) {
    friend.pins = pins.filter(pin => oldPins.includes(pin));
    delete friend.directory;
    friend.devices = [];
    renderFriends(); renderChat();
    throw error;
  }
  renderFriends(); renderChat();
  if (invite && !approved) throw new Error('Invite fingerprint, device or relay does not match the current directory.');
  return directory;
}

// Only a definitive version conflict, which the relay guarantees was not
// enqueued, may retry. Track accepted recipients throughout a fan-out.
async function sendWithDirectory(friend, text, kind, target, delivered) {
  let directory = cachedDirectory(friend);
  if (!directory || !friend.devices?.length) directory = await readFriendDirectory(friend);
  const sent = new Set();
  for (let attempt = 0; attempt < 3; attempt++) {
    const eligible = directory.entries.filter(row => (!target || row.device === target) && trustedEntry(friend, row));
    if (!eligible.length && !sent.size) throw new Error('No verified active device. Add its invite after checking the fingerprint.');
    try {
      for (const entry of eligible) {
        if (sent.has(entry.device)) continue;
        const guard = {friend, directory, entry};
        const tag = await sendToDevice(friend.username, entry.device, text, kind, guard);
        sent.add(entry.device);
        if (delivered) delivered(entry.device, tag);
      }
      return [...sent];
    } catch (error) {
      if (error.status !== 409 || error.code !== 'DIRECTORY_CHANGED') throw error;
      directory = await readFriendDirectory(friend);
    }
  }
  throw new Error('Device directory kept changing. Delivered to: ' + ([...sent].join(', ') || 'no devices'));
}
