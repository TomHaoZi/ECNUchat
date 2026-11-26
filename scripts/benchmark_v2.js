'use strict';
// Local two-endpoint experiment on the PWA crypto modules. No relay or user data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const readline = require('node:readline/promises');
const {execFileSync} = require('node:child_process');
const {setTimeout: sleep} = require('node:timers/promises');
const C = require('../v2/pwa/crypto.js');
const PQ = require('../v2/pwa/crypto-pq.js');

function device(name, hybrid) {
  const id = C.generateIdentity(name);
  const pq = hybrid ? PQ.generatePqForIdentity(id) : null;
  return {name, id, pq, bundle: C.bundleFromIdentity(id), pqBundle: pq && PQ.pqBundleFrom(pq)};
}

function directory(mode) {
  return [device('alice', mode === 'hybrid'), device('bobby', mode === 'hybrid')];
}

function route(from, to) {
  return {sender: from + ':phone', recipient: to + ':phone',
    protocol_version: 'v1', message_type: 'text', kind: 'chat'};
}

// Round-trip the same UTF-8 JSON body that app.js posts to /v1/envelopes.
function transfer(body) {
  const bytes = Buffer.from(JSON.stringify(body));
  return {received: JSON.parse(bytes.toString('utf8')), size: bytes.length};
}

function deliver(payload, from, to) {
  return transfer({...route(from, to), ...payload,
    x3dh: payload.x3dh || null, ...(payload.pq_ref ? {} : {pq_ct: payload.pq_ct || null})});
}

function deviceRoute(from, to) {
  return {localAddress: from + ':phone', remoteAddress: to + ':phone'};
}

async function firstMessage(peers, index, text, references = false) {
  const [a, b] = peers;
  const hybrid = !!a.pq;
  assert.ok(!references || hybrid);
  // A consuming fetch serves one OPK and one PQOPK. Each test session uses
  // its own entry. The receiver sees the sender's full public directory row.
  const raw = {...b.bundle, opk_pub: b.bundle.opks[index]};
  delete raw.opks;
  const bob = C.parseBundle(raw, b.name);
  let sender;
  if (hybrid) {
    const parsed = PQ.parsePqBundle({...b.pqBundle, pq_opks: [b.pqBundle.pq_opks[index]]},
      b.name, bob.ik_sign_pub);
    const handshake = await PQ.pqxdhInitiatorSecret(a.id, bob, parsed, a.pq.pqPub);
    assert.equal(handshake.handshakePq, 'pqopk');
    sender = await PQ.createHybridInitiatorSession(a.name, b.name, a.id, bob,
      handshake, parsed.pqPub, a.pq.pqSeed);
  } else {
    sender = await C.createInitiatorSession(a.name, b.name, a.id, bob);
  }
  const encrypt = hybrid ? PQ.hybridSessionEncrypt : C.sessionEncrypt;
  const decrypt = hybrid ? PQ.hybridSessionDecrypt : C.sessionDecrypt;
  const outgoing = references ? deviceRoute(a.name, b.name) : undefined;
  const incoming = references ? deviceRoute(b.name, a.name) : undefined;
  const {received, size} = deliver(await encrypt(sender, text, 'chat', outgoing), a.name, b.name);
  const alice = C.parseBundle(a.bundle, a.name);
  if (hybrid) PQ.parsePqBundle(a.pqBundle, a.name, alice.ik_sign_pub);
  const initial = received.x3dh;
  PQ.assertReceiverMode(hybrid, initial);
  const receiver = hybrid
    ? await PQ.createHybridReceiverSession(b.name, a.name, b.id, b.pq,
        alice.ik_sign_pub, alice.ik_dh_pub, initial)
    : await C.createReceiverSession(b.name, a.name, b.id,
        alice.ik_sign_pub, alice.ik_dh_pub, initial);
  assert.equal(await decrypt(receiver, received, incoming), text);
  if (references) {
    assert.ok(received.pq_ct && !received.pq_ref);
    const receipt = transfer(receiver.pqReceipt).received;
    assert.equal(await PQ.acceptPqReceipt(sender, receipt, outgoing), true);
  }
  return {sessions: [sender, receiver], encrypt, decrypt, size, references};
}

async function chat(link, reverse, text) {
  const from = link.sessions[reverse ? 1 : 0];
  const to = link.sessions[reverse ? 0 : 1];
  const outgoing = link.references ? deviceRoute(from.localUser, to.localUser) : undefined;
  const incoming = link.references ? deviceRoute(to.localUser, from.localUser) : undefined;
  const payload = await link.encrypt(from, text, 'chat', outgoing);
  const {received, size} = deliver(payload, from.localUser, to.localUser);
  assert.equal(await link.decrypt(to, received, incoming), text);
  if (link.references) assert.ok(received.pq_ref && !received.pq_ct && !to.pqReceipt);
  return size;
}

async function baseline(mode, text) {
  const header = route('alice', 'bobby');
  if (mode === 'plain') return async () => {
    const {received, size} = transfer({...header, body: C.wrapInnerText(text, 'chat')});
    assert.equal(C.parseInnerText(received.body, received), text);
    return size;
  };
  const key = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']);
  const aad = Buffer.from(JSON.stringify(header));
  return async () => {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const raw = Buffer.from(C.wrapInnerText(text, 'chat'));
    const encrypted = await crypto.subtle.encrypt({name: 'AES-GCM', iv, additionalData: aad}, key, raw);
    const {received, size} = transfer({...header, nonce: Buffer.from(iv).toString('base64'),
      ciphertext: Buffer.from(encrypted).toString('base64')});
    const decrypted = await crypto.subtle.decrypt({name: 'AES-GCM', iv: Buffer.from(received.nonce, 'base64'),
      additionalData: aad}, key, Buffer.from(received.ciphertext, 'base64'));
    assert.equal(C.parseInnerText(Buffer.from(decrypted).toString(), received), text);
    return size;
  };
}

async function measure(count, operation) {
  let totalBytes = 0;
  const cpuStart = process.cpuUsage();
  const start = performance.now();
  for (let i = 0; i < count; i++) totalBytes += await operation(i);
  const wallMs = performance.now() - start;
  const cpu = process.cpuUsage(cpuStart);
  return {count, wall_ms: wallMs, cpu_ms: (cpu.user + cpu.system) / 1000, envelope_bytes: totalBytes};
}

const modes = ['plain', 'aes', 'classic', 'hybrid'];
async function runRound(round, warmup) {
  const rows = [];
  // Reverse successive rounds to balance thermal and order effects.
  for (const mode of round % 2 ? [...modes].reverse() : modes) {
    const ratchet = mode === 'classic' || mode === 'hybrid';
    const peers = ratchet && directory(mode);
    let keyIndex = 0;
    for (const [scenario, bytes] of [['first', 128], ['same', 128], ['alternate', 128], ['same', 4096]]) {
      if (!ratchet && scenario !== 'same') continue;
      const text = 'x'.repeat(bytes);
      let operation, count;
      if (!ratchet) {
        operation = await baseline(mode, text);
        count = mode === 'plain' ? 20000 : 1200;
      } else if (scenario === 'first') {
        operation = async () => (await firstMessage(peers, keyIndex++, text)).size;
        count = 4;
      } else {
        const link = await firstMessage(peers, keyIndex++, 'initialize');
        operation = i => chat(link, scenario === 'alternate' && i % 2 === 0, text);
        count = scenario === 'alternate' ? 40 : 320;
      }
      rows.push({round, mode, scenario, body_bytes: bytes,
        ...await measure(warmup ? Math.min(4, count) : count, operation)});
    }
  }
  return rows;
}

async function memoryRun(mode) {
  const hybrid = mode === 'hybrid';
  const peers = directory(mode);
  const link = await firstMessage(peers, 0, 'x'.repeat(128));
  for (let i = 0; i < 64; i++) await chat(link, i % 2 === 0, 'x'.repeat(128));
  const pack = hybrid ? PQ.hybridSessionToJSON : C.sessionToJSON;
  const stateBytes = link.sessions.map(s => Buffer.byteLength(JSON.stringify(pack(s))));
  return {mode, peak_rss_kib: process.resourceUsage().maxRSS, session_json_bytes: stateBytes};
}

async function paced(mode, count, interval) {
  if (!['classic', 'hybrid', 'idle'].includes(mode) || !Number.isSafeInteger(count) || count < 1 ||
      !Number.isFinite(interval) || interval <= 0) throw Error('Invalid paced workload');
  const text = 'x'.repeat(128);
  const link = mode === 'idle' ? null : await firstMessage(directory(mode), 0, text);
  if (link) for (let i = 0; i < 8; i++) await chat(link, i % 2 === 0, text);
  const input = readline.createInterface({input: process.stdin});
  const go = input[Symbol.asyncIterator]().next();
  console.log('READY');
  if ((await go).done) throw Error('Expected a start line');
  input.close();
  const start = performance.now();
  let maxLateness = 0;
  let missed = 0;
  for (let i = 0; i < count; i++) {
    const lateness = performance.now() - (start + i * interval);
    maxLateness = Math.max(maxLateness, lateness);
    if (lateness >= interval) missed++;
    if (link) await chat(link, i % 2 === 0, text);
    const delay = start + (i + 1) * interval - performance.now();
    if (delay > 0) await sleep(delay);
  }
  console.log(JSON.stringify({count: link ? count : 0, slots: count, elapsed_ms: performance.now() - start,
    max_lateness_ms: maxLateness, missed_slots: missed}));
}

async function main() {
  const [arg, mode, count, interval] = process.argv.slice(2);
  if (arg === '--paced') return paced(mode, Number(count), Number(interval));
  if (arg === '--memory') return console.log(JSON.stringify(await memoryRun(mode)));
  if (arg === '--smoke') return console.log(JSON.stringify(await runRound(0, true)));
  const rounds = 8;
  const batches = [];
  await runRound(0, true);
  for (let i = 0; i < rounds; i++) batches.push(...await runRound(i + 1, false));
  const memory = [];
  for (let i = 0; i < 3; i++) {
    for (const mode of ['classic', 'hybrid']) {
      memory.push(JSON.parse(execFileSync(process.execPath, [__filename, '--memory', mode], {encoding: 'utf8'})));
    }
  }
  const result = {runtime: process.version, v8: process.versions.v8, os: os.version(),
    cpu: os.cpus()[0].model, rounds, measured_at: new Date().toISOString(), batches, memory};
  const file = arg || path.join(__dirname, '../docs/benchmarks/v2.json');
  fs.mkdirSync(path.dirname(file), {recursive: true});
  fs.writeFileSync(file, JSON.stringify(result, null, 2) + '\n');
  console.log(file);
}

module.exports = {directory, firstMessage, chat};
if (require.main === module) {
  main().catch(error => { console.error(error); process.exitCode = 1; });
}
