export type CustomError = InvalidWormholeMessage | DeserializeMessageFailed | InvalidPriceUpdate | UnsupportedMessageType | InvalidDataSource | InsufficientFunds | WrongWriteAuthority | WrongVaaOwner | DeserializeVaaFailed | InsufficientGuardianSignatures | InvalidVaaVersion | GuardianSetMismatch | InvalidGuardianOrder | InvalidGuardianIndex | InvalidSignature | InvalidGuardianKeyRecovery | WrongGuardianSetOwner | InvalidGuardianSetPda | GuardianSetExpired | GovernanceAuthorityMismatch | TargetGovernanceAuthorityMismatch | NonexistentGovernanceAuthorityTransferRequest;
export declare class InvalidWormholeMessage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6000;
    readonly code = 6000;
    readonly name = "InvalidWormholeMessage";
    readonly msg = "Received an invalid wormhole message";
    constructor(logs?: string[] | undefined);
}
export declare class DeserializeMessageFailed extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6001;
    readonly code = 6001;
    readonly name = "DeserializeMessageFailed";
    readonly msg = "An error occurred when deserializing the message";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPriceUpdate extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6002;
    readonly code = 6002;
    readonly name = "InvalidPriceUpdate";
    readonly msg = "Received an invalid price update";
    constructor(logs?: string[] | undefined);
}
export declare class UnsupportedMessageType extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6003;
    readonly code = 6003;
    readonly name = "UnsupportedMessageType";
    readonly msg = "This type of message is not supported currently";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidDataSource extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6004;
    readonly code = 6004;
    readonly name = "InvalidDataSource";
    readonly msg = "The tuple emitter chain, emitter doesn't match one of the valid data sources.";
    constructor(logs?: string[] | undefined);
}
export declare class InsufficientFunds extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6005;
    readonly code = 6005;
    readonly name = "InsufficientFunds";
    readonly msg = "Funds are insufficient to pay the receiving fee";
    constructor(logs?: string[] | undefined);
}
export declare class WrongWriteAuthority extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6006;
    readonly code = 6006;
    readonly name = "WrongWriteAuthority";
    readonly msg = "This signer can't write to price update account";
    constructor(logs?: string[] | undefined);
}
export declare class WrongVaaOwner extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6007;
    readonly code = 6007;
    readonly name = "WrongVaaOwner";
    readonly msg = "The posted VAA account has the wrong owner.";
    constructor(logs?: string[] | undefined);
}
export declare class DeserializeVaaFailed extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6008;
    readonly code = 6008;
    readonly name = "DeserializeVaaFailed";
    readonly msg = "An error occurred when deserializing the VAA.";
    constructor(logs?: string[] | undefined);
}
export declare class InsufficientGuardianSignatures extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6009;
    readonly code = 6009;
    readonly name = "InsufficientGuardianSignatures";
    readonly msg = "The number of guardian signatures is below the minimum";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidVaaVersion extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6010;
    readonly code = 6010;
    readonly name = "InvalidVaaVersion";
    readonly msg = "Invalid VAA version";
    constructor(logs?: string[] | undefined);
}
export declare class GuardianSetMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6011;
    readonly code = 6011;
    readonly name = "GuardianSetMismatch";
    readonly msg = "Guardian set version in the VAA doesn't match the guardian set passed";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidGuardianOrder extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6012;
    readonly code = 6012;
    readonly name = "InvalidGuardianOrder";
    readonly msg = "Guardian signature indices must be increasing";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidGuardianIndex extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6013;
    readonly code = 6013;
    readonly name = "InvalidGuardianIndex";
    readonly msg = "Guardian index exceeds the number of guardians in the set";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidSignature extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6014;
    readonly code = 6014;
    readonly name = "InvalidSignature";
    readonly msg = "A VAA signature is invalid";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidGuardianKeyRecovery extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6015;
    readonly code = 6015;
    readonly name = "InvalidGuardianKeyRecovery";
    readonly msg = "The recovered guardian public key doesn't match the guardian set";
    constructor(logs?: string[] | undefined);
}
export declare class WrongGuardianSetOwner extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6016;
    readonly code = 6016;
    readonly name = "WrongGuardianSetOwner";
    readonly msg = "The guardian set account is owned by the wrong program";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidGuardianSetPda extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6017;
    readonly code = 6017;
    readonly name = "InvalidGuardianSetPda";
    readonly msg = "The Guardian Set account doesn't match the PDA derivation";
    constructor(logs?: string[] | undefined);
}
export declare class GuardianSetExpired extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6018;
    readonly code = 6018;
    readonly name = "GuardianSetExpired";
    readonly msg = "The Guardian Set is expired";
    constructor(logs?: string[] | undefined);
}
export declare class GovernanceAuthorityMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6019;
    readonly code = 6019;
    readonly name = "GovernanceAuthorityMismatch";
    readonly msg = "The signer is not authorized to perform this governance action";
    constructor(logs?: string[] | undefined);
}
export declare class TargetGovernanceAuthorityMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6020;
    readonly code = 6020;
    readonly name = "TargetGovernanceAuthorityMismatch";
    readonly msg = "The signer is not authorized to accept the governance authority";
    constructor(logs?: string[] | undefined);
}
export declare class NonexistentGovernanceAuthorityTransferRequest extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6021;
    readonly code = 6021;
    readonly name = "NonexistentGovernanceAuthorityTransferRequest";
    readonly msg = "The governance authority needs to request a transfer first";
    constructor(logs?: string[] | undefined);
}
export declare function fromCode(code: number, logs?: string[]): CustomError | null;
//# sourceMappingURL=custom.d.ts.map