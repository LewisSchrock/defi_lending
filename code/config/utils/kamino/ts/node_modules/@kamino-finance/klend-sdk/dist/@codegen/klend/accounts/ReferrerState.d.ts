import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface ReferrerStateFields {
    shortUrl: Address;
    owner: Address;
}
export interface ReferrerStateJSON {
    shortUrl: string;
    owner: string;
}
export declare class ReferrerState {
    readonly shortUrl: Address;
    readonly owner: Address;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<ReferrerState>;
    constructor(fields: ReferrerStateFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<ReferrerState | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<ReferrerState | null>>;
    static decode(data: Buffer): ReferrerState;
    toJSON(): ReferrerStateJSON;
    static fromJSON(obj: ReferrerStateJSON): ReferrerState;
}
//# sourceMappingURL=ReferrerState.d.ts.map