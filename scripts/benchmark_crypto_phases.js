'use strict';

// Time the two PWA crypto endpoints on a single host. Each run uses fresh keys.
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const {directory, firstMessage, chat} = require('./benchmark_v2.js');

const root = path.resolve(__dirname, '..');
const orders = ['FEC', 'FCE', 'EFC', 'ECF', 'CFE', 'CEF'];
const messages = Array.from({length: 11}, (_, index) =>
  ('Message ' + String(index).padStart(3, '0') + ' ').padEnd(128, 'x'));

async function run(arm) {
  const peers = directory(arm === 'F' ? 'classic' : 'hybrid');
  const start = performance.now();
  const link = await firstMessage(peers, 0, messages[0], arm === 'C');
  const established = performance.now();
  for (const message of messages.slice(1)) await chat(link, false, message);
  const delivered = performance.now();
  return {arm, cold_ms: established - start, warm_ten_ms: delivered - established};
}

async function main() {
  for (const arm of 'FECCEF') await run(arm);
  const runs = [];
  for (let block = 0; block < 24; block++) {
    const order = orders[block % orders.length];
    for (const [position, arm] of [...order].entries()) {
      runs.push({block: block + 1, position: position + 1, ...await run(arm)});
    }
  }
  const files = ['scripts/benchmark_crypto_phases.js', 'scripts/benchmark_v2.js',
    'v2/pwa/crypto.js', 'v2/pwa/crypto-pq.js'];
  const sha256 = Object.fromEntries(files.map(file => [file,
    createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')]));
  const report = {
    measured_at: new Date().toISOString(), runtime: process.version, v8: process.versions.v8,
    os: os.version(), cpu: os.cpus()[0].model, clocks: 'performance.now() elapsed milliseconds',
    arms: {F: 'classic', E: 'hybrid full', C: 'hybrid authenticated reference'},
    design: 'All six arm orders repeated four times. Two discarded warm-up runs per arm. Fresh identities and prekeys per run.',
    cold: 'Both-end bundle verification, session creation, first 128-byte message encryption/decryption, including authenticated receipt for C.',
    warm: 'Ten sequential same-direction 128-byte message encrypt/decrypt pairs. C already confirmed.',
    boundary: 'Includes UTF-8 JSON envelope roundtrip and plaintext equality check. Excludes key pool creation, UI, disk, directory I/O and relay.',
    sha256, runs
  };
  const output = path.join(root, 'docs/benchmarks/three-schemes-compute.json');
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  console.log(output, runs.length + ' verified sessions');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
