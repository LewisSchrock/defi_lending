import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface ReferrerTokenStateFields {
    /** Pubkey of the referrer/owner */
    referrer: Address;
    /** Token mint for the account */
    mint: Address;
    /** Amount that has been accumulated and not claimed yet -> available to claim (scaled fraction) */
    amountUnclaimedSf: BN;
    /** Amount that has been accumulated in total -> both already claimed and unclaimed (scaled fraction) */
    amountCumulativeSf: BN;
    /** Referrer token state bump, used for address validation */
    bump: BN;
    padding: Array<BN>;
}
export interface ReferrerTokenStateJSON {
    /** Pubkey of the referrer/owner */
    referrer: string;
    /** Token mint for the account */
    mint: string;
    /** Amount that has been accumulated and not claimed yet -> available to claim (scaled fraction) */
    amountUnclaimedSf: string;
    /** Amount that has been accumulated in total -> both already claimed and unclaimed (scaled fraction) */
    amountCumulativeSf: string;
    /** Referrer token state bump, used for address validation */
    bump: string;
    padding: Array<string>;
}
/** Referrer account -> each owner can have multiple accounts for specific reserves */
export declare class ReferrerTokenState {
    /** Pubkey of the referrer/owner */
    readonly referrer: Address;
    /** Token mint for the account */
    readonly mint: Address;
    /** Amount that has been accumulated and not claimed yet -> available to claim (scaled fraction) */
    readonly amountUnclaimedSf: BN;
    /** Amount that has been accumulated in total -> both already claimed and unclaimed (scaled fraction) */
    readonly amountCumulativeSf: BN;
    /** Referrer token state bump, used for address validation */
    readonly bump: BN;
    readonly padding: Array<BN>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<ReferrerTokenState>;
    constructor(fields: ReferrerTokenStateFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<ReferrerTokenState | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<ReferrerTokenState | null>>;
    static decode(data: Buffer): ReferrerTokenState;
    toJSON(): ReferrerTokenStateJSON;
    static fromJSON(obj: ReferrerTokenStateJSON): ReferrerTokenState;
}
//# sourceMappingURL=ReferrerTokenState.d.ts.map