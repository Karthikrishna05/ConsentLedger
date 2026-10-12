
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { network } from "hardhat";

describe("ConsentRegistry", async function () {
  const { viem } = await network.create();
  const publicClient = await viem.getPublicClient();
  const walletClients = await viem.getWalletClients();

  it("creates and grants consent, then accepts the correct hash", async function () {
    const registry = await viem.deployContract("ConsentRegistry");
    const owner = walletClients[0];
    const consentId = `0x${"11".repeat(32)}` as `0x${string}`;
    const artefactHash = `0x${"22".repeat(32)}` as `0x${string}`;
    const expiry = BigInt(Math.floor(Date.now() / 1000) + 3600);
    const nonce = 1n;

    await registry.write.createConsent([
      consentId,
      artefactHash,
      expiry,
      nonce,
    ]);

    await registry.write.grantConsent([consentId]);

    const valid = await registry.read.isValid([
      consentId,
      artefactHash,
    ]);

    assert.equal(valid, true);
  });

  it("rejects a tampered document hash", async function () {
    const registry = await viem.deployContract("ConsentRegistry");
    const consentId = `0x${"33".repeat(32)}` as `0x${string}`;
    const artefactHash = `0x${"44".repeat(32)}` as `0x${string}`;
    const tamperedHash = `0x${"55".repeat(32)}` as `0x${string}`;
    const expiry = BigInt(Math.floor(Date.now() / 1000) + 3600);

    await registry.write.createConsent([
      consentId,
      artefactHash,
      expiry,
      2n,
    ]);

    await registry.write.grantConsent([consentId]);

    const valid = await registry.read.isValid([
      consentId,
      tamperedHash,
    ]);

    assert.equal(valid, false);
  });

  it("rejects consent after it has been revoked", async function () {
    const registry = await viem.deployContract("ConsentRegistry");
    const consentId = `0x${"66".repeat(32)}` as `0x${string}`;
    const artefactHash = `0x${"77".repeat(32)}` as `0x${string}`;
    const expiry = BigInt(Math.floor(Date.now() / 1000) + 3600);

    await registry.write.createConsent([
      consentId,
      artefactHash,
      expiry,
      3n,
    ]);

    await registry.write.grantConsent([consentId]);
    await registry.write.revokeConsent([consentId]);

    const valid = await registry.read.isValid([
      consentId,
      artefactHash,
    ]);

    assert.equal(valid, false);
  });
});
