import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface SbStateFields {
    authority: Address;
    tokenMint: Address;
    tokenVault: Address;
    daoMint: Address;
    ebuf: Array<number>;
}
export interface SbStateJSON {
    authority: string;
    tokenMint: string;
    tokenVault: string;
    daoMint: string;
    ebuf: Array<number>;
}
export declare class SbState {
    readonly authority: Address;
    readonly tokenMint: Address;
    readonly tokenVault: Address;
    readonly daoMint: Address;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<SbState>;
    constructor(fields: SbStateFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<SbState | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<SbState | null>>;
    static decode(data: Buffer): SbState;
    toJSON(): SbStateJSON;
    static fromJSON(obj: SbStateJSON): SbState;
}
//# sourceMappingURL=SbState.d.ts.map