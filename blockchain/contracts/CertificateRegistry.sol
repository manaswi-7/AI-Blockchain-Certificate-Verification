// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract CertificateRegistry {
    struct Record {
        bytes32 documentHash;
        uint256 timestamp;
        address issuer;
        bool exists;
    }

    mapping(bytes32 => Record) private records;

    event CertificateAnchored(bytes32 indexed certificateId, bytes32 indexed documentHash, address indexed issuer);

    function anchorCertificate(bytes32 certificateId, bytes32 documentHash) external {
        require(certificateId != bytes32(0), "Invalid certificate ID");
        require(documentHash != bytes32(0), "Invalid document hash");
        require(!records[certificateId].exists, "Certificate already anchored");
        records[certificateId] = Record(documentHash, block.timestamp, msg.sender, true);
        emit CertificateAnchored(certificateId, documentHash, msg.sender);
    }

    function verifyCertificate(bytes32 certificateId, bytes32 documentHash) external view returns (bool) {
        Record memory r = records[certificateId];
        return r.exists && r.documentHash == documentHash;
    }

    function getCertificate(bytes32 certificateId) external view returns (bytes32, uint256, address, bool) {
        Record memory r = records[certificateId];
        return (r.documentHash, r.timestamp, r.issuer, r.exists);
    }
}
