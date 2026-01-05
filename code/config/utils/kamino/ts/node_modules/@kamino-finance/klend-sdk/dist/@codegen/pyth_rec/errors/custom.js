"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NonexistentGovernanceAuthorityTransferRequest = exports.TargetGovernanceAuthorityMismatch = exports.GovernanceAuthorityMismatch = exports.GuardianSetExpired = exports.InvalidGuardianSetPda = exports.WrongGuardianSetOwner = exports.InvalidGuardianKeyRecovery = exports.InvalidSignature = exports.InvalidGuardianIndex = exports.InvalidGuardianOrder = exports.GuardianSetMismatch = exports.InvalidVaaVersion = exports.InsufficientGuardianSignatures = exports.DeserializeVaaFailed = exports.WrongVaaOwner = exports.WrongWriteAuthority = exports.InsufficientFunds = exports.InvalidDataSource = exports.UnsupportedMessageType = exports.InvalidPriceUpdate = exports.DeserializeMessageFailed = exports.InvalidWormholeMessage = void 0;
exports.fromCode = fromCode;
class InvalidWormholeMessage extends Error {
    logs;
    static code = 6000;
    code = 6000;
    name = "InvalidWormholeMessage";
    msg = "Received an invalid wormhole message";
    constructor(logs) {
        super("6000: Received an invalid wormhole message");
        this.logs = logs;
    }
}
exports.InvalidWormholeMessage = InvalidWormholeMessage;
class DeserializeMessageFailed extends Error {
    logs;
    static code = 6001;
    code = 6001;
    name = "DeserializeMessageFailed";
    msg = "An error occurred when deserializing the message";
    constructor(logs) {
        super("6001: An error occurred when deserializing the message");
        this.logs = logs;
    }
}
exports.DeserializeMessageFailed = DeserializeMessageFailed;
class InvalidPriceUpdate extends Error {
    logs;
    static code = 6002;
    code = 6002;
    name = "InvalidPriceUpdate";
    msg = "Received an invalid price update";
    constructor(logs) {
        super("6002: Received an invalid price update");
        this.logs = logs;
    }
}
exports.InvalidPriceUpdate = InvalidPriceUpdate;
class UnsupportedMessageType extends Error {
    logs;
    static code = 6003;
    code = 6003;
    name = "UnsupportedMessageType";
    msg = "This type of message is not supported currently";
    constructor(logs) {
        super("6003: This type of message is not supported currently");
        this.logs = logs;
    }
}
exports.UnsupportedMessageType = UnsupportedMessageType;
class InvalidDataSource extends Error {
    logs;
    static code = 6004;
    code = 6004;
    name = "InvalidDataSource";
    msg = "The tuple emitter chain, emitter doesn't match one of the valid data sources.";
    constructor(logs) {
        super("6004: The tuple emitter chain, emitter doesn't match one of the valid data sources.");
        this.logs = logs;
    }
}
exports.InvalidDataSource = InvalidDataSource;
class InsufficientFunds extends Error {
    logs;
    static code = 6005;
    code = 6005;
    name = "InsufficientFunds";
    msg = "Funds are insufficient to pay the receiving fee";
    constructor(logs) {
        super("6005: Funds are insufficient to pay the receiving fee");
        this.logs = logs;
    }
}
exports.InsufficientFunds = InsufficientFunds;
class WrongWriteAuthority extends Error {
    logs;
    static code = 6006;
    code = 6006;
    name = "WrongWriteAuthority";
    msg = "This signer can't write to price update account";
    constructor(logs) {
        super("6006: This signer can't write to price update account");
        this.logs = logs;
    }
}
exports.WrongWriteAuthority = WrongWriteAuthority;
class WrongVaaOwner extends Error {
    logs;
    static code = 6007;
    code = 6007;
    name = "WrongVaaOwner";
    msg = "The posted VAA account has the wrong owner.";
    constructor(logs) {
        super("6007: The posted VAA account has the wrong owner.");
        this.logs = logs;
    }
}
exports.WrongVaaOwner = WrongVaaOwner;
class DeserializeVaaFailed extends Error {
    logs;
    static code = 6008;
    code = 6008;
    name = "DeserializeVaaFailed";
    msg = "An error occurred when deserializing the VAA.";
    constructor(logs) {
        super("6008: An error occurred when deserializing the VAA.");
        this.logs = logs;
    }
}
exports.DeserializeVaaFailed = DeserializeVaaFailed;
class InsufficientGuardianSignatures extends Error {
    logs;
    static code = 6009;
    code = 6009;
    name = "InsufficientGuardianSignatures";
    msg = "The number of guardian signatures is below the minimum";
    constructor(logs) {
        super("6009: The number of guardian signatures is below the minimum");
        this.logs = logs;
    }
}
exports.InsufficientGuardianSignatures = InsufficientGuardianSignatures;
class InvalidVaaVersion extends Error {
    logs;
    static code = 6010;
    code = 6010;
    name = "InvalidVaaVersion";
    msg = "Invalid VAA version";
    constructor(logs) {
        super("6010: Invalid VAA version");
        this.logs = logs;
    }
}
exports.InvalidVaaVersion = InvalidVaaVersion;
class GuardianSetMismatch extends Error {
    logs;
    static code = 6011;
    code = 6011;
    name = "GuardianSetMismatch";
    msg = "Guardian set version in the VAA doesn't match the guardian set passed";
    constructor(logs) {
        super("6011: Guardian set version in the VAA doesn't match the guardian set passed");
        this.logs = logs;
    }
}
exports.GuardianSetMismatch = GuardianSetMismatch;
class InvalidGuardianOrder extends Error {
    logs;
    static code = 6012;
    code = 6012;
    name = "InvalidGuardianOrder";
    msg = "Guardian signature indices must be increasing";
    constructor(logs) {
        super("6012: Guardian signature indices must be increasing");
        this.logs = logs;
    }
}
exports.InvalidGuardianOrder = InvalidGuardianOrder;
class InvalidGuardianIndex extends Error {
    logs;
    static code = 6013;
    code = 6013;
    name = "InvalidGuardianIndex";
    msg = "Guardian index exceeds the number of guardians in the set";
    constructor(logs) {
        super("6013: Guardian index exceeds the number of guardians in the set");
        this.logs = logs;
    }
}
exports.InvalidGuardianIndex = InvalidGuardianIndex;
class InvalidSignature extends Error {
    logs;
    static code = 6014;
    code = 6014;
    name = "InvalidSignature";
    msg = "A VAA signature is invalid";
    constructor(logs) {
        super("6014: A VAA signature is invalid");
        this.logs = logs;
    }
}
exports.InvalidSignature = InvalidSignature;
class InvalidGuardianKeyRecovery extends Error {
    logs;
    static code = 6015;
    code = 6015;
    name = "InvalidGuardianKeyRecovery";
    msg = "The recovered guardian public key doesn't match the guardian set";
    constructor(logs) {
        super("6015: The recovered guardian public key doesn't match the guardian set");
        this.logs = logs;
    }
}
exports.InvalidGuardianKeyRecovery = InvalidGuardianKeyRecovery;
class WrongGuardianSetOwner extends Error {
    logs;
    static code = 6016;
    code = 6016;
    name = "WrongGuardianSetOwner";
    msg = "The guardian set account is owned by the wrong program";
    constructor(logs) {
        super("6016: The guardian set account is owned by the wrong program");
        this.logs = logs;
    }
}
exports.WrongGuardianSetOwner = WrongGuardianSetOwner;
class InvalidGuardianSetPda extends Error {
    logs;
    static code = 6017;
    code = 6017;
    name = "InvalidGuardianSetPda";
    msg = "The Guardian Set account doesn't match the PDA derivation";
    constructor(logs) {
        super("6017: The Guardian Set account doesn't match the PDA derivation");
        this.logs = logs;
    }
}
exports.InvalidGuardianSetPda = InvalidGuardianSetPda;
class GuardianSetExpired extends Error {
    logs;
    static code = 6018;
    code = 6018;
    name = "GuardianSetExpired";
    msg = "The Guardian Set is expired";
    constructor(logs) {
        super("6018: The Guardian Set is expired");
        this.logs = logs;
    }
}
exports.GuardianSetExpired = GuardianSetExpired;
class GovernanceAuthorityMismatch extends Error {
    logs;
    static code = 6019;
    code = 6019;
    name = "GovernanceAuthorityMismatch";
    msg = "The signer is not authorized to perform this governance action";
    constructor(logs) {
        super("6019: The signer is not authorized to perform this governance action");
        this.logs = logs;
    }
}
exports.GovernanceAuthorityMismatch = GovernanceAuthorityMismatch;
class TargetGovernanceAuthorityMismatch extends Error {
    logs;
    static code = 6020;
    code = 6020;
    name = "TargetGovernanceAuthorityMismatch";
    msg = "The signer is not authorized to accept the governance authority";
    constructor(logs) {
        super("6020: The signer is not authorized to accept the governance authority");
        this.logs = logs;
    }
}
exports.TargetGovernanceAuthorityMismatch = TargetGovernanceAuthorityMismatch;
class NonexistentGovernanceAuthorityTransferRequest extends Error {
    logs;
    static code = 6021;
    code = 6021;
    name = "NonexistentGovernanceAuthorityTransferRequest";
    msg = "The governance authority needs to request a transfer first";
    constructor(logs) {
        super("6021: The governance authority needs to request a transfer first");
        this.logs = logs;
    }
}
exports.NonexistentGovernanceAuthorityTransferRequest = NonexistentGovernanceAuthorityTransferRequest;
function fromCode(code, logs) {
    switch (code) {
        case 6000:
            return new InvalidWormholeMessage(logs);
        case 6001:
            return new DeserializeMessageFailed(logs);
        case 6002:
            return new InvalidPriceUpdate(logs);
        case 6003:
            return new UnsupportedMessageType(logs);
        case 6004:
            return new InvalidDataSource(logs);
        case 6005:
            return new InsufficientFunds(logs);
        case 6006:
            return new WrongWriteAuthority(logs);
        case 6007:
            return new WrongVaaOwner(logs);
        case 6008:
            return new DeserializeVaaFailed(logs);
        case 6009:
            return new InsufficientGuardianSignatures(logs);
        case 6010:
            return new InvalidVaaVersion(logs);
        case 6011:
            return new GuardianSetMismatch(logs);
        case 6012:
            return new InvalidGuardianOrder(logs);
        case 6013:
            return new InvalidGuardianIndex(logs);
        case 6014:
            return new InvalidSignature(logs);
        case 6015:
            return new InvalidGuardianKeyRecovery(logs);
        case 6016:
            return new WrongGuardianSetOwner(logs);
        case 6017:
            return new InvalidGuardianSetPda(logs);
        case 6018:
            return new GuardianSetExpired(logs);
        case 6019:
            return new GovernanceAuthorityMismatch(logs);
        case 6020:
            return new TargetGovernanceAuthorityMismatch(logs);
        case 6021:
            return new NonexistentGovernanceAuthorityTransferRequest(logs);
    }
    return null;
}
//# sourceMappingURL=custom.js.map