'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const C = require('../pwa/crypto.js');
const PQ = require('../pwa/crypto-pq.js');

const aliceRoute = {localAddress: 'alice:phone', remoteAddress: 'bobby:laptop'};
const bobRoute = {localAddress: aliceRoute.remoteAddress, remoteAddress: aliceRoute.localAddress};

function device(name) {
  const id = C.generateIdentity(name);
  const pq = PQ.generatePqForIdentity(id);
  return {id, pq};
}

const alice = device('alice');
const bob = device('bobby');

async function send(session, text, route, legacy = false) {
  const payload = await PQ.hybridSessionEncrypt(session, text, 'chat', legacy ? undefined : route);
  return JSON.parse(JSON.stringify({
    sender: route.localAddress, recipient: route.remoteAddress,
    protocol_version: 'v1', message_type: 'text', ...payload
  }));
}

async function pair(legacy = false) {
  const rawBob = C.bundleFromIdentity(bob.id);
  const bobKeys = C.parseBundle({...rawBob, opk_pub: rawBob.opks[0]}, 'bobby');
  const pqBundle = PQ.pqBundleFrom(bob.pq);
  const bobPq = PQ.parsePqBundle({...pqBundle, pq_opks: pqBundle.pq_opks.slice(0, 1)},
    'bobby', bobKeys.ik_sign_pub);
  const handshake = await PQ.pqxdhInitiatorSecret(alice.id, bobKeys, bobPq, alice.pq.pqPub);
  const a = await PQ.createHybridInitiatorSession('alice', 'bobby', alice.id, bobKeys, handshake,
    bobPq.pqPub, alice.pq.pqSeed);
  const first = await send(a, 'first', aliceRoute, legacy);
  const b = await PQ.createHybridReceiverSession('bobby', 'alice', bob.id, bob.pq,
    alice.id.ikSign.publicKey, alice.id.ikDh.publicKey, first.x3dh);
  return {a, b, first};
}

function full(packet) {
  assert.equal(Buffer.from(packet.pq_ct, 'base64').length, 1088);
  assert.ok(!packet.pq_ref);
}

function reference(packet, receipt) {
  assert.ok(!packet.pq_ct, 'an acknowledged chain should omit the full ML-KEM ciphertext');
  assert.ok(receipt.pq_ref);
  assert.equal(packet.pq_ref, receipt.pq_ref);
}

function snapshot(session) {
  return JSON.stringify(PQ.hybridSessionToJSON(session));
}

function restore(state, peer) {
  return PQ.hybridSessionFromJSON(JSON.parse(state), peer.id, peer.pq.pqSeed);
}

async function rejectData(session, packet, route, reason) {
  const before = snapshot(session);
  await assert.rejects(() => PQ.hybridSessionDecrypt(session, packet, route), reason);
  assert.equal(snapshot(session) === before, true, 'rejected data changed persisted session state');
  assert.ok(!session.pqReceipt, 'rejected data must not produce a receipt');
}

async function rejectReceipt(session, receipt, route) {
  const before = snapshot(session);
  const accepted = await PQ.acceptPqReceipt(session, receipt, route).catch(() => false);
  assert.equal(accepted, false);
  assert.equal(snapshot(session) === before, true, 'rejected receipt changed persisted session state');
}

function flip(value) {
  const bytes = Buffer.from(value, 'base64');
  bytes[0] ^= 1;
  return bytes.toString('base64');
}

test('the sender repeats the full encapsulation until an authenticated receipt arrives', async () => {
  const {a, b, first} = await pair();
  full(first);
  assert.equal(await PQ.hybridSessionDecrypt(b, first, bobRoute), 'first');
  const droppedAck = b.pqReceipt;
  assert.ok(droppedAck, 'a receiver must provide a receipt after authenticating a full packet');
  const droppedData = await send(a, 'dropped full', aliceRoute);
  full(droppedData);
  const retry = await send(a, 'another full', aliceRoute);
  full(retry);
  assert.equal(retry.pq_ct, first.pq_ct);
  await rejectData(b, {...retry, pq_ct: flip(retry.pq_ct)}, bobRoute,
    'a repeated full packet must still authenticate the original encapsulation');
  assert.equal(await PQ.hybridSessionDecrypt(b, retry, bobRoute), 'another full');
  const receipt = JSON.parse(JSON.stringify(b.pqReceipt));
  assert.equal(receipt.sender, bobRoute.localAddress);
  assert.equal(receipt.recipient, bobRoute.remoteAddress);
  assert.equal(receipt.protocol_version, 'v1');
  assert.equal(receipt.message_type, 'pq_ack_v1');
  assert.equal(receipt.dh_pub, retry.dh_pub);
  assert.ok(receipt.ciphertext);
  assert.equal(await PQ.acceptPqReceipt(a, receipt, aliceRoute), true);
  const compact = await send(a, 'another full', aliceRoute);
  reference(compact, receipt);
  assert.ok(Buffer.byteLength(JSON.stringify(compact)) < Buffer.byteLength(JSON.stringify(retry)),
    'the same chat text should take fewer wire bytes after acknowledgment');
  assert.equal(await PQ.hybridSessionDecrypt(b, compact, bobRoute), 'another full');
  assert.equal(b.pqReceipt, null, 'a reference must not trigger a receipt loop');
  assert.equal(await PQ.hybridSessionDecrypt(b, droppedData, bobRoute), 'dropped full');
});

test('a receipt in transit can unlock references after both devices restart', async () => {
  let {a, b, first} = await pair();
  assert.equal(await PQ.hybridSessionDecrypt(b, first, bobRoute), 'first');
  assert.ok(b.pqReceipt, 'the authenticated full packet should produce a receipt to queue');
  const queuedReceipt = JSON.stringify(b.pqReceipt);
  a = restore(snapshot(a), alice);
  b = restore(snapshot(b), bob);
  full(await send(a, 'still pending', aliceRoute));
  const receipt = JSON.parse(queuedReceipt);
  assert.equal(await PQ.acceptPqReceipt(a, receipt, aliceRoute), true);
  a = restore(snapshot(a), alice);
  const delayed = await send(a, 'delayed', aliceRoute);
  const onTime = await send(a, 'on time', aliceRoute);
  reference(delayed, receipt);
  reference(onTime, receipt);
  assert.equal(await PQ.hybridSessionDecrypt(b, onTime, bobRoute), 'on time');
  b = restore(snapshot(b), bob);
  assert.equal(await PQ.hybridSessionDecrypt(b, delayed, bobRoute), 'delayed');
  await rejectData(b, delayed, bobRoute, 'replayed reference');
});

test('references enforce the 40-key reorder window and remain recoverable after a restart', async () => {
  const {a, b, first} = await pair();
  await PQ.hybridSessionDecrypt(b, first, bobRoute);
  const receipt = b.pqReceipt;
  assert.equal(await PQ.acceptPqReceipt(a, receipt, aliceRoute), true);
  const packets = [];
  for (let index = 0; index < 42; index++) {
    const packet = await send(a, String(index), aliceRoute);
    reference(packet, receipt);
    packets.push(packet);
  }
  const before = snapshot(b);
  await assert.rejects(PQ.hybridSessionDecrypt(b, packets[41], bobRoute), /skip limit/i);
  assert.equal(snapshot(b) === before, true, '41 missing keys must leave the persisted state intact');
  assert.equal(b.pqReceipt, null);
  assert.equal(await PQ.hybridSessionDecrypt(b, packets[40], bobRoute), '40');
  const resumed = restore(snapshot(b), bob);
  assert.equal(await PQ.hybridSessionDecrypt(resumed, packets[41], bobRoute), '41');
  for (let index = 39; index >= 0; index--) {
    assert.equal(await PQ.hybridSessionDecrypt(resumed, packets[index], bobRoute), String(index));
  }
  await rejectData(resumed, packets[0], bobRoute, 'duplicate after draining skipped keys');
});

test('tampering or misrouting a full packet cannot install a reference or advance the ratchet', async () => {
  const {b, first} = await pair();
  const tablet = {...bobRoute, localAddress: 'bobby:tablet'};
  const otherSender = {...bobRoute, remoteAddress: 'alice:tablet'};
  await rejectData(b, {...first, recipient: tablet.localAddress}, tablet, 'wrong recipient device');
  await rejectData(b, {...first, sender: otherSender.remoteAddress}, otherSender, 'wrong sender device');
  await rejectData(b, {...first, pq_ct: null}, bobRoute, 'missing hybrid encapsulation');
  await rejectData(b, {...first, pq_ct: flip(first.pq_ct)}, bobRoute, 'bad encapsulation');
  await rejectData(b, {...first, ciphertext: flip(first.ciphertext)}, bobRoute, 'bad GCM ciphertext');
  assert.equal(await PQ.hybridSessionDecrypt(b, first, bobRoute), 'first');
  assert.ok(b.pqReceipt);
  await rejectData(b, first, bobRoute, 'replayed full packet');
});

test('only the peer device that received the current encapsulation can acknowledge it', async () => {
  const {a, b, first} = await pair();
  await PQ.hybridSessionDecrypt(b, first, bobRoute);
  const receipt = b.pqReceipt;
  const otherSender = {...aliceRoute, remoteAddress: 'bobby:phone'};
  const otherRecipient = {...aliceRoute, localAddress: 'alice:laptop'};
  await rejectReceipt(a, {...receipt, sender: otherSender.remoteAddress}, otherSender);
  await rejectReceipt(a, {...receipt, recipient: otherRecipient.localAddress}, otherRecipient);
  await rejectReceipt(a, {...receipt, ciphertext: flip(receipt.ciphertext)}, aliceRoute);
  await rejectReceipt(a, {...receipt, dh_pub: flip(receipt.dh_pub)}, aliceRoute);
  await rejectReceipt(a, {...receipt, pq_ref: flip(receipt.pq_ref)}, aliceRoute);
  await rejectReceipt(a, {...receipt, message_type: 'text'}, aliceRoute);
  full(await send(a, 'waiting for the genuine receipt', aliceRoute));
  assert.equal(await PQ.acceptPqReceipt(a, receipt, aliceRoute), true);
  reference(await send(a, 'accepted', aliceRoute), receipt);
});

test('a reference requires its authenticated full packet, device pair and untampered ciphertext', async () => {
  const {a, b, first} = await pair();
  const beforeFull = snapshot(b);
  await PQ.hybridSessionDecrypt(b, first, bobRoute);
  const receipt = b.pqReceipt;
  assert.equal(await PQ.acceptPqReceipt(a, receipt, aliceRoute), true);
  const compact = await send(a, 'compact', aliceRoute);
  reference(compact, receipt);
  await rejectData(restore(beforeFull, bob), compact, bobRoute, 'unknown reference');
  const tablet = {...bobRoute, localAddress: 'bobby:tablet'};
  await rejectData(b, {...compact, recipient: tablet.localAddress}, tablet, 'wrong device');
  await rejectData(b, {...compact, pq_ref: null}, bobRoute, 'stripped reference');
  const wrongRef = (compact.pq_ref[0] === 'a' ? 'b' : 'a') + compact.pq_ref.slice(1);
  await rejectData(b, {...compact, pq_ref: wrongRef}, bobRoute, 'incorrect reference');
  await rejectData(b, {...compact, pq_ct: first.pq_ct}, bobRoute, 'ambiguous full and reference');
  await rejectData(b, {...compact, pq_ref: null, pq_ct: first.pq_ct}, bobRoute,
    'a reference packet cannot be relabeled as a full packet');
  await rejectData(b, {...compact, ciphertext: flip(compact.ciphertext)}, bobRoute, 'bad GCM tag');
  assert.equal(await PQ.hybridSessionDecrypt(b, compact, bobRoute), 'compact');
});

test('a new DH chain survives a lost first full packet and retains skipped references from the old chain', async () => {
  let {a, b, first} = await pair();
  await PQ.hybridSessionDecrypt(b, first, bobRoute);
  const oldReceipt = b.pqReceipt;
  assert.equal(await PQ.acceptPqReceipt(a, oldReceipt, aliceRoute), true);
  const lateOld = await send(a, 'late old reference', aliceRoute);
  reference(lateOld, oldReceipt);
  const answer = await send(b, 'reverse direction', bobRoute);
  full(answer);
  assert.equal(await PQ.hybridSessionDecrypt(a, answer, aliceRoute), 'reverse direction');
  await rejectReceipt(a, oldReceipt, aliceRoute);
  const lostFull = await send(a, 'new chain start', aliceRoute);
  full(lostFull);
  assert.notEqual(lostFull.dh_pub, first.dh_pub);
  assert.notEqual(lostFull.pq_ct, first.pq_ct);
  const next = await send(a, 'new chain retry', aliceRoute);
  full(next);
  assert.equal(next.dh_pub, lostFull.dh_pub);
  assert.equal(next.pq_ct, lostFull.pq_ct);
  assert.equal(await PQ.hybridSessionDecrypt(b, next, bobRoute), 'new chain retry');
  const newReceipt = b.pqReceipt;
  assert.notEqual(newReceipt.pq_ref, oldReceipt.pq_ref);
  assert.equal(await PQ.acceptPqReceipt(a, newReceipt, aliceRoute), true);
  const nextRef = await send(a, 'new reference', aliceRoute);
  reference(nextRef, newReceipt);
  b = restore(snapshot(b), bob);
  await rejectData(b, {...lateOld, pq_ref: newReceipt.pq_ref}, bobRoute, 'reference from another chain');
  assert.equal(await PQ.hybridSessionDecrypt(b, lateOld, bobRoute), 'late old reference');
  await rejectData(b, lateOld, bobRoute, 'replay from retired chain');
  assert.equal(await PQ.hybridSessionDecrypt(b, lostFull, bobRoute), 'new chain start');
  assert.equal(await PQ.hybridSessionDecrypt(b, nextRef, bobRoute), 'new reference');
});

// Fields written by the original PWA. Restoring only this shape exercises
// migration even when the current serializer adds defaults to new records.
function legacyRecord(session) {
  const record = PQ.hybridSessionToJSON(session);
  const fields = ['localUser', 'remoteUser', 'mode', 'remotePqPub', 'rk', 'dhs_priv',
    'dhs_pub', 'dhs_pq_ct', 'dhr_pub', 'cks', 'ckr', 'ns', 'nr', 'pns', 'skipped',
    'seen', 'retired', 'pendingSk', 'initialSent'];
  return JSON.stringify(Object.fromEntries(fields.map(field => [field, record[field]])));
}

test('a sender working with a legacy receiver keeps full packets readable with the original v1 AAD', async () => {
  const {a, b, first} = await pair();
  assert.equal(await PQ.hybridSessionDecrypt(b, first), 'first');
  assert.ok(!b.pqReceipt);
  const receiver = JSON.parse(legacyRecord(b));
  const packet = await send(a, 'legacy receiver', aliceRoute);
  full(packet);
  const {mk} = await C.kdfCk(C.unb64(receiver.ckr));
  const aad = C.buildAad('alice', 'bobby', packet.n, packet.pn, C.unb64(packet.dh_pub));
  const raw = await C.aesGcmDecrypt(mk, C.unb64(packet.nonce), C.unb64(packet.ciphertext), aad);
  assert.equal(C.parseInnerText(new TextDecoder().decode(raw), packet), 'legacy receiver');
});

test('upgraded devices can resume original persisted sessions and receive legacy full packets', async () => {
  let {a, b, first} = await pair(true);
  assert.equal(await PQ.hybridSessionDecrypt(b, first, bobRoute), 'first');
  assert.ok(!b.pqReceipt, 'a legacy sender has not requested receipts');
  a = restore(legacyRecord(a), alice);
  b = restore(legacyRecord(b), bob);
  const next = await send(a, 'legacy sender', aliceRoute, true);
  full(next);
  await rejectData(b, {...next, pq_ct: null}, bobRoute, 'a migrated hybrid session must still reject downgrades');
  assert.equal(await PQ.hybridSessionDecrypt(b, next, bobRoute), 'legacy sender');
  assert.ok(!b.pqReceipt);
  const reply = await send(b, 'upgraded sender', bobRoute);
  full(reply);
  assert.equal(await PQ.hybridSessionDecrypt(a, reply, aliceRoute), 'upgraded sender');
  assert.equal(await PQ.acceptPqReceipt(b, a.pqReceipt, bobRoute), true);
  const compact = await send(b, 'migrated reference', bobRoute);
  reference(compact, a.pqReceipt);
  assert.equal(await PQ.hybridSessionDecrypt(a, compact, aliceRoute), 'migrated reference');
});
