import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface CrankAccountDataFields {
    name: Array<number>;
    metadata: Array<number>;
    queuePubkey: Address;
    pqSize: number;
    maxRows: number;
    jitterModifier: number;
    ebuf: Array<number>;
    dataBuffer: Address;
}
export interface CrankAccountDataJSON {
    name: Array<number>;
    metadata: Array<number>;
    queuePubkey: string;
    pqSize: number;
    maxRows: number;
    jitterModifier: number;
    ebuf: Array<number>;
    dataBuffer: string;
}
export declare class CrankAccountData {
    readonly name: Array<number>;
    readonly metadata: Array<number>;
    readonly queuePubkey: Address;
    readonly pqSize: number;
    readonly maxRows: number;
    readonly jitterModifier: number;
    readonly ebuf: Array<number>;
    readonly dataBuffer: Address;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<CrankAccountData>;
    constructor(fields: CrankAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<CrankAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<CrankAccountData | null>>;
    static decode(data: Buffer): CrankAccountData;
    toJSON(): CrankAccountDataJSON;
    static fromJSON(obj: CrankAccountDataJSON): CrankAccountData;
}
//# sourceMappingURL=CrankAccountData.d.ts.map