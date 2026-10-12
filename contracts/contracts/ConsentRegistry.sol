
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title ConsentRegistry
/// @notice Stores consent fingerprints, not personal data.
contract ConsentRegistry {
    enum Status {
        NONE,
        CREATED,
        GRANTED,
        REVOKED
    }

    struct Consent {
        bytes32 artefactHash;
        address owner;
        uint64 expiry;
        uint256 nonce;
        Status status;
    }

    mapping(bytes32 => Consent) public consents;

    event ConsentCreated(
        bytes32 indexed consentId,
        bytes32 artefactHash,
        uint64 expiry,
        uint256 nonce
    );

    event ConsentGranted(bytes32 indexed consentId);
    event ConsentRevoked(bytes32 indexed consentId);

    event AccessRecorded(
        bytes32 indexed consentId,
        bytes32 presentedHash,
        bool valid
    );

    /// Create a consent record.
    function createConsent(
        bytes32 consentId,
        bytes32 artefactHash,
        uint64 expiry,
        uint256 nonce
    ) external {
        require(
            consents[consentId].status == Status.NONE,
            "consent exists"
        );

        consents[consentId] = Consent({
            artefactHash: artefactHash,
            owner: msg.sender,
            expiry: expiry,
            nonce: nonce,
            status: Status.CREATED
        });

        emit ConsentCreated(consentId, artefactHash, expiry, nonce);
    }

    /// Grant consent. Only its owner can grant it.
    function grantConsent(bytes32 consentId) external {
        Consent storage c = consents[consentId];

        require(c.status == Status.CREATED, "not in created state");
        require(c.owner == msg.sender, "not owner");

        c.status = Status.GRANTED;

        emit ConsentGranted(consentId);
    }

    /// Revoke previously granted consent.
    function revokeConsent(bytes32 consentId) external {
        Consent storage c = consents[consentId];

        require(c.status == Status.GRANTED, "not granted");
        require(c.owner == msg.sender, "not owner");

        c.status = Status.REVOKED;

        emit ConsentRevoked(consentId);
    }

    /// Verify access and record the result on-chain.
    function recordAccess(
        bytes32 consentId,
        bytes32 presentedHash
    ) external returns (bool valid) {
        Consent storage c = consents[consentId];

        valid = (
            c.status == Status.GRANTED &&
            block.timestamp <= c.expiry &&
            c.artefactHash == presentedHash
        );

        emit AccessRecorded(consentId, presentedHash, valid);
    }

    /// Read-only consent verification.
    function isValid(
        bytes32 consentId,
        bytes32 presentedHash
    ) external view returns (bool) {
        Consent storage c = consents[consentId];

        return (
            c.status == Status.GRANTED &&
            block.timestamp <= c.expiry &&
            c.artefactHash == presentedHash
        );
    }
}
