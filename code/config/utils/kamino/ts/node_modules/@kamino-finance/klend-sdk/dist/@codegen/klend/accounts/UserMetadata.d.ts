import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface UserMetadataFields {
    /** Pubkey of the referrer/owner - pubkey::default if no referrer */
    referrer: Address;
    /** Bump used for validation of account address */
    bump: BN;
    /** User lookup table - used to store all user accounts - atas for each reserve mint, each obligation PDA, UserMetadata itself and all referrer_token_states if there is a referrer */
    userLookupTable: Address;
    /** User metadata account owner */
    owner: Address;
    padding1: Array<BN>;
    padding2: Array<BN>;
}
export interface UserMetadataJSON {
    /** Pubkey of the referrer/owner - pubkey::default if no referrer */
    referrer: string;
    /** Bump used for validation of account address */
    bump: string;
    /** User lookup table - used to store all user accounts - atas for each reserve mint, each obligation PDA, UserMetadata itself and all referrer_token_states if there is a referrer */
    userLookupTable: string;
    /** User metadata account owner */
    owner: string;
    padding1: Array<string>;
    padding2: Array<string>;
}
/** Referrer account -> each owner can have multiple accounts for specific reserves */
export declare class UserMetadata {
    /** Pubkey of the referrer/owner - pubkey::default if no referrer */
    readonly referrer: Address;
    /** Bump used for validation of account address */
    readonly bump: BN;
    /** User lookup table - used to store all user accounts - atas for each reserve mint, each obligation PDA, UserMetadata itself and all referrer_token_states if there is a referrer */
    readonly userLookupTable: Address;
    /** User metadata account owner */
    readonly owner: Address;
    readonly padding1: Array<BN>;
    readonly padding2: Array<BN>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<UserMetadata>;
    constructor(fields: UserMetadataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<UserMetadata | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<UserMetadata | null>>;
    static decode(data: Buffer): UserMetadata;
    toJSON(): UserMetadataJSON;
    static fromJSON(obj: UserMetadataJSON): UserMetadata;
}
//# sourceMappingURL=UserMetadata.d.ts.map