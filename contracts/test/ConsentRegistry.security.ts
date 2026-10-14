import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { network } from "hardhat";
import { encodeAbiParameters, keccak256 } from "viem";

type Hex = `0x${string}`;

describe("ConsentRegistry security", async function () {
  const { viem, networkHelpers } = await network.create();
  const publicClient = await viem.getPublicClient();
  const [owner, attacker, stranger] = await viem.getWalletClients();
  const HASH = `0x${"aa".repeat(32)}` as Hex;
  const OTHER = `0x${"bb".repeat(32)}` as Hex;
  const now = async () => (await publicClient.getBlock()).timestamp;

  // create (and optionally grant) a consent as `who`; returns the registry and the id the contract assigned
  async function setup(who = owner, nonce = 1n, grant = true, ttl = 3600n) {
    const registry = await viem.deployContract("ConsentRegistry");
    await registry.write.createConsent([HASH, (await now()) + ttl, nonce], { account: who.account });
    const id = await registry.read.consentIdFor([who.account.address, HASH, nonce]);
    if (grant) await registry.write.grantConsent([id], { account: who.account });
    return { registry, id };
  }

  it("the id is computed on-chain from owner + hash + nonce", async function () {
    const { registry, id } = await setup();
    const expected = keccak256(
      encodeAbiParameters(
        [{ type: "address" }, { type: "bytes32" }, { type: "uint256" }],
        [owner.account.address, HASH, 1n],
      ),
    );
    assert.equal(id, expected);
    const created = await publicClient.getContractEvents({
      address: registry.address, abi: registry.abi, eventName: "ConsentCreated", fromBlock: 0n,
    });
    assert.equal(created[0].args.consentId, id);
    assert.equal(created[0].args.owner!.toLowerCase(), owner.account.address.toLowerCase());
  });

  it("nobody can take another owner's id (same hash and nonce give a different id)", async function () {
    const registry = await viem.deployContract("ConsentRegistry");
    const expiry = (await now()) + 3600n;
    await registry.write.createConsent([HASH, expiry, 7n], { account: attacker.account });
    await registry.write.createConsent([HASH, expiry, 7n], { account: owner.account }); // not blocked
    const ownerId = await registry.read.consentIdFor([owner.account.address, HASH, 7n]);
    const attackerId = await registry.read.consentIdFor([attacker.account.address, HASH, 7n]);
    assert.notEqual(ownerId, attackerId);
    assert.equal((await registry.read.consents([ownerId]))[1].toLowerCase(), owner.account.address.toLowerCase());
  });

  it("recordAccess leaves an audit entry that says who asked and whether it was valid", async function () {
    const { registry, id } = await setup();
    await registry.write.recordAccess([id, HASH], { account: stranger.account });
    await registry.write.recordAccess([id, OTHER], { account: attacker.account }); // tampered document
    const log = await publicClient.getContractEvents({
      address: registry.address, abi: registry.abi, eventName: "AccessRecorded", fromBlock: 0n,
    });
    assert.deepEqual(log.map((e) => e.args.valid), [true, false]);
    assert.deepEqual(
      log.map((e) => e.args.accessor!.toLowerCase()),
      [stranger.account.address.toLowerCase(), attacker.account.address.toLowerCase()],
    );
  });

  it("only the owner can grant or revoke", async function () {
    const { registry, id } = await setup(owner, 2n, false);
    await assert.rejects(registry.write.grantConsent([id], { account: attacker.account }), /not owner/);
    await registry.write.grantConsent([id]);
    await assert.rejects(registry.write.revokeConsent([id], { account: attacker.account }), /not owner/);
    assert.equal(await registry.read.isValid([id, HASH]), true);
  });

  it("a revoked consent stays revoked, and a created one can be cancelled", async function () {
    const { registry, id } = await setup(owner, 3n);
    await registry.write.revokeConsent([id]);
    assert.equal(await registry.read.isValid([id, HASH]), false);
    await assert.rejects(registry.write.grantConsent([id]), /not in created state/);
    await assert.rejects(registry.write.revokeConsent([id]), /not active/);
    const fresh = await setup(owner, 4n, false);
    await fresh.registry.write.revokeConsent([fresh.id]); // cancel before granting
    assert.equal((await fresh.registry.read.consents([fresh.id]))[4], 3);
  });

  it("the same owner cannot register the same hash and nonce twice", async function () {
    const { registry } = await setup(owner, 5n);
    await assert.rejects(registry.write.createConsent([HASH, (await now()) + 3600n, 5n]), /consent exists/);
  });

  it("expiry: refused once the time has passed, and a past expiry cannot be created", async function () {
    const { registry, id } = await setup(owner, 6n, true, 100n);
    assert.equal(await registry.read.isValid([id, HASH]), true);
    await networkHelpers.time.increase(200);
    assert.equal(await registry.read.isValid([id, HASH]), false);
    await registry.write.recordAccess([id, HASH]);
    const log = await publicClient.getContractEvents({
      address: registry.address, abi: registry.abi, eventName: "AccessRecorded", fromBlock: 0n,
    });
    assert.equal(log[log.length - 1].args.valid, false);
    await assert.rejects(registry.write.createConsent([HASH, 1n, 99n]), /expiry in past/);
  });
});
