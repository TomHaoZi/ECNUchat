'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('../pwa/crypto.js');
const PQ = require('../pwa/crypto-pq.js');

for (const hybrid of [false, true]) {
  test((hybrid ? 'Hybrid' : 'Classical') + ' call signalling shares the text ratchet', async () => {
    const alice = C.generateIdentity('alice');
    const bob = C.generateIdentity('bob');
    const bundle = C.parseBundle(C.bundleFromIdentity(bob), 'bob');
    const bobPq = hybrid && PQ.generatePqForIdentity(bob);
    let sender;
    if (hybrid) {
      const alicePq = PQ.generatePqForIdentity(alice);
      const pqBundle = PQ.parsePqBundle(PQ.pqBundleFrom(bobPq), 'bob', bundle.ik_sign_pub);
      const handshake = await PQ.pqxdhInitiatorSecret(alice, bundle, pqBundle, alicePq.pqPub);
      sender = await PQ.createHybridInitiatorSession('alice', 'bob', alice, bundle,
        handshake, bobPq.pqPub, alicePq.pqSeed);
    } else {
      sender = await C.createInitiatorSession('alice', 'bob', alice, bundle);
    }
    const encrypt = hybrid ? PQ.hybridSessionEncrypt : C.sessionEncrypt;
    const decrypt = hybrid ? PQ.hybridSessionDecrypt : C.sessionDecrypt;
    const signal = JSON.stringify({type: 'call-invite', call_id: 'local-test'});
    const envelope = await encrypt(sender, signal, 'call');
    assert.equal(envelope.kind, 'call');
    const receiver = hybrid
      ? await PQ.createHybridReceiverSession('bob', 'alice', bob, bobPq,
          alice.ikSign.publicKey, alice.ikDh.publicKey, envelope.x3dh)
      : await C.createReceiverSession('bob', 'alice', bob,
          alice.ikSign.publicKey, alice.ikDh.publicKey, envelope.x3dh);
    await assert.rejects(decrypt(receiver, {...envelope, kind: 'chat'}), /kind/i);
    assert.equal(await decrypt(receiver, envelope), signal);
    const reply = await encrypt(receiver, 'Hello after the call');
    assert.equal(reply.kind, 'chat');
    assert.equal(await decrypt(sender, reply), 'Hello after the call');
  });
}
