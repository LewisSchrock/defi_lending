import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import * as types from "../types";
export interface SlidingResultAccountDataFields {
    data: Array<types.SlidingWindowElementFields>;
    bump: number;
    ebuf: Array<number>;
}
export interface SlidingResultAccountDataJSON {
    data: Array<types.SlidingWindowElementJSON>;
    bump: number;
    ebuf: Array<number>;
}
export declare class SlidingResultAccountData {
    readonly data: Array<types.SlidingWindowElement>;
    readonly bump: number;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<SlidingResultAccountData>;
    constructor(fields: SlidingResultAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<SlidingResultAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<SlidingResultAccountData | null>>;
    static decode(data: Buffer): SlidingResultAccountData;
    toJSON(): SlidingResultAccountDataJSON;
    static fromJSON(obj: SlidingResultAccountDataJSON): SlidingResultAccountData;
}
//# sourceMappingURL=SlidingResultAccountData.d.ts.map