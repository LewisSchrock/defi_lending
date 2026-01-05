import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface VrfPoolAccountDataFields {
    authority: Address;
    queue: Address;
    escrow: Address;
    minInterval: number;
    maxRows: number;
    size: number;
    idx: number;
    stateBump: number;
    ebuf: Array<number>;
}
export interface VrfPoolAccountDataJSON {
    authority: string;
    queue: string;
    escrow: string;
    minInterval: number;
    maxRows: number;
    size: number;
    idx: number;
    stateBump: number;
    ebuf: Array<number>;
}
export declare class VrfPoolAccountData {
    readonly authority: Address;
    readonly queue: Address;
    readonly escrow: Address;
    readonly minInterval: number;
    readonly maxRows: number;
    readonly size: number;
    readonly idx: number;
    readonly stateBump: number;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<VrfPoolAccountData>;
    constructor(fields: VrfPoolAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<VrfPoolAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<VrfPoolAccountData | null>>;
    static decode(data: Buffer): VrfPoolAccountData;
    toJSON(): VrfPoolAccountDataJSON;
    static fromJSON(obj: VrfPoolAccountDataJSON): VrfPoolAccountData;
}
//# sourceMappingURL=VrfPoolAccountData.d.ts.map