import { Address } from "@solana/kit";
import * as types from "../types";
export interface PythConfigurationFields {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    price: Address;
}
export interface PythConfigurationJSON {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    price: string;
}
export declare class PythConfiguration {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    readonly price: Address;
    constructor(fields: PythConfigurationFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PythConfiguration;
    static toEncodable(fields: PythConfigurationFields): {
        price: Address;
    };
    toJSON(): PythConfigurationJSON;
    static fromJSON(obj: PythConfigurationJSON): PythConfiguration;
    toEncodable(): {
        price: Address;
    };
}
//# sourceMappingURL=PythConfiguration.d.ts.map