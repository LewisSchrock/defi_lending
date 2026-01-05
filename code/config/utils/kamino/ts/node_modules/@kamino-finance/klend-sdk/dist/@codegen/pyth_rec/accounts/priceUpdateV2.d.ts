import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface priceUpdateV2Fields {
    writeAuthority: Address;
    verificationLevel: types.VerificationLevelKind;
    priceMessage: types.PriceFeedMessageFields;
    postedSlot: BN;
}
export interface priceUpdateV2JSON {
    writeAuthority: string;
    verificationLevel: types.VerificationLevelJSON;
    priceMessage: types.PriceFeedMessageJSON;
    postedSlot: string;
}
export declare class priceUpdateV2 {
    readonly writeAuthority: Address;
    readonly verificationLevel: types.VerificationLevelKind;
    readonly priceMessage: types.PriceFeedMessage;
    readonly postedSlot: BN;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<priceUpdateV2>;
    constructor(fields: priceUpdateV2Fields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<priceUpdateV2 | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<priceUpdateV2 | null>>;
    static decode(data: Buffer): priceUpdateV2;
    toJSON(): priceUpdateV2JSON;
    static fromJSON(obj: priceUpdateV2JSON): priceUpdateV2;
}
//# sourceMappingURL=priceUpdateV2.d.ts.map