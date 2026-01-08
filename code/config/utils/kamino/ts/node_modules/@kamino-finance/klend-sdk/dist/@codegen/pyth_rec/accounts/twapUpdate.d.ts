import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import * as types from "../types";
export interface twapUpdateFields {
    writeAuthority: Address;
    twap: types.TwapPriceFields;
}
export interface twapUpdateJSON {
    writeAuthority: string;
    twap: types.TwapPriceJSON;
}
export declare class twapUpdate {
    readonly writeAuthority: Address;
    readonly twap: types.TwapPrice;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<twapUpdate>;
    constructor(fields: twapUpdateFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<twapUpdate | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<twapUpdate | null>>;
    static decode(data: Buffer): twapUpdate;
    toJSON(): twapUpdateJSON;
    static fromJSON(obj: twapUpdateJSON): twapUpdate;
}
//# sourceMappingURL=twapUpdate.d.ts.map