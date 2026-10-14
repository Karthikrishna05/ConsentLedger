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
        address indexed owner,
        bytes32 artefactHash,
        uint64 expiry,
        uint256 nonce
    );

    event ConsentGranted(bytes32 indexed consentId);
    event ConsentRevoked(bytes32 indexed consentId);

    event AccessRecorded(
        bytes32 indexed consentId,
        address indexed accessor,
        bytes32 presentedHash,
        bool valid
    );

    /// The id a given owner gets for a given fingerprint and nonce. Nobody else can obtain it.
    function consentIdFor(
        address owner,
        bytes32 artefactHash,
        uint256 nonce
    ) public pure returns (bytes32) {
        return keccak256(abi.encode(owner, artefactHash, nonce));
    }

    /// Create a consent record. The id is computed here, from the caller's own address.
    function createConsent(
        bytes32 artefactHash,
        uint64 expiry,
        uint256 nonce
    ) external returns (bytes32 consentId) {
        require(expiry > block.timestamp, "expiry in past");

        consentId = consentIdFor(msg.sender, artefactHash, nonce);

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

        emit ConsentCreated(consentId, msg.sender, artefactHash, expiry, nonce);
    }

    /// Grant consent. Only its owner can grant it.
    function grantConsent(bytes32 consentId) external {
        Consent storage c = consents[consentId];

        require(c.status == Status.CREATED, "not in created state");
        require(c.owner == msg.sender, "not owner");

        c.status = Status.GRANTED;

        emit ConsentGranted(consentId);
    }

    /// Revoke a consent that was created or granted. Only its owner can.
    function revokeConsent(bytes32 consentId) external {
        Consent storage c = consents[consentId];

        require(
            c.status == Status.CREATED || c.status == Status.GRANTED,
            "not active"
        );
        require(c.owner == msg.sender, "not owner");

        c.status = Status.REVOKED;

        emit ConsentRevoked(consentId);
    }

    /// Verify access and record the result, and who asked, on-chain.
    function recordAccess(
        bytes32 consentId,
        bytes32 presentedHash
    ) external returns (bool valid) {
        valid = isValid(consentId, presentedHash);

        emit AccessRecorded(consentId, msg.sender, presentedHash, valid);
    }

    /// Read-only consent verification.
    function isValid(
        bytes32 consentId,
        bytes32 presentedHash
    ) public view returns (bool) {
        Consent storage c = consents[consentId];

        return (
            c.status == Status.GRANTED &&
            block.timestamp <= c.expiry &&
            c.artefactHash == presentedHash
        );
    }
}
