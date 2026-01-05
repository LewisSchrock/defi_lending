import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface TestOracleFields {
    price: BN;
    expo: number;
    conf: BN;
    publishTime: BN;
}
export interface TestOracleJSON {
    price: string;
    expo: number;
    conf: string;
    publishTime: string;
}
export declare class TestOracle {
    readonly price: BN;
    readonly expo: number;
    readonly conf: BN;
    readonly publishTime: BN;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<TestOracle>;
    constructor(fields: TestOracleFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<TestOracle | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<TestOracle | null>>;
    static decode(data: Buffer): TestOracle;
    toJSON(): TestOracleJSON;
    static fromJSON(obj: TestOracleJSON): TestOracle;
}
//# sourceMappingURL=TestOracle.d.ts.map