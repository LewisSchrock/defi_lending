import { Address } from "@solana/kit";
import * as types from "../types";
export interface ProgramConfigParamsFields {
    token: Address;
    bump: number;
    daoMint: Address;
}
export interface ProgramConfigParamsJSON {
    token: string;
    bump: number;
    daoMint: string;
}
export declare class ProgramConfigParams {
    readonly token: Address;
    readonly bump: number;
    readonly daoMint: Address;
    constructor(fields: ProgramConfigParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ProgramConfigParams;
    static toEncodable(fields: ProgramConfigParamsFields): {
        token: Address;
        bump: number;
        daoMint: Address;
    };
    toJSON(): ProgramConfigParamsJSON;
    static fromJSON(obj: ProgramConfigParamsJSON): ProgramConfigParams;
    toEncodable(): {
        token: Address;
        bump: number;
        daoMint: Address;
    };
}
//# sourceMappingURL=ProgramConfigParams.d.ts.map