import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface GlobalConfigFields {
    /** Global admin of the program */
    globalAdmin: Address;
    /** Pending admin must sign a specific transaction to become the global admin */
    pendingAdmin: Address;
    /** Fee collector is the only allowed owner of token accounts receiving protocol fees */
    feeCollector: Address;
    /** Padding to make the struct size 1024 bytes */
    padding: Array<number>;
}
export interface GlobalConfigJSON {
    /** Global admin of the program */
    globalAdmin: string;
    /** Pending admin must sign a specific transaction to become the global admin */
    pendingAdmin: string;
    /** Fee collector is the only allowed owner of token accounts receiving protocol fees */
    feeCollector: string;
    /** Padding to make the struct size 1024 bytes */
    padding: Array<number>;
}
export declare class GlobalConfig {
    /** Global admin of the program */
    readonly globalAdmin: Address;
    /** Pending admin must sign a specific transaction to become the global admin */
    readonly pendingAdmin: Address;
    /** Fee collector is the only allowed owner of token accounts receiving protocol fees */
    readonly feeCollector: Address;
    /** Padding to make the struct size 1024 bytes */
    readonly padding: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<GlobalConfig>;
    constructor(fields: GlobalConfigFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<GlobalConfig | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<GlobalConfig | null>>;
    static decode(data: Buffer): GlobalConfig;
    toJSON(): GlobalConfigJSON;
    static fromJSON(obj: GlobalConfigJSON): GlobalConfig;
}
//# sourceMappingURL=GlobalConfig.d.ts.map