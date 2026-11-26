'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const { resolveRelayUrl } = require('./config.js');

test('desktop accepts IPv4, IPv6 and named loopback HTTP relays', () => {
  for (const url of ['http://127.0.0.1:9000', 'http://[::1]:9000', 'http://localhost:9000']) {
    assert.equal(resolveRelayUrl({ storedRelayUrl: url }), url);
  }
  assert.throws(() => resolveRelayUrl({ storedRelayUrl: 'http://remote.invalid' }));
});

test('environment and file settings take priority over the saved PWA relay', () => {
  const stored = { storedRelayUrl: 'https://saved.invalid' };
  const file = { ...stored, fileConfig: { relayUrl: 'https://file.invalid/' } };
  assert.equal(resolveRelayUrl(), 'http://127.0.0.1:8765');
  assert.equal(resolveRelayUrl(stored), 'https://saved.invalid');
  assert.equal(resolveRelayUrl(file), 'https://file.invalid');
  assert.equal(resolveRelayUrl({ ...file, envRelayUrl: 'https://env.invalid/' }), 'https://env.invalid');
});
