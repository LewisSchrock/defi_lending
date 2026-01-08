import { Address } from "@solana/kit";
import * as types from "../types";
export interface ScopeConfigurationFields {
    /** Pubkey of the scope price feed (disabled if `null` or `default`) */
    priceFeed: Address;
    /** This is the scope_id price chain that results in a price for the token */
    priceChain: Array<number>;
    /** This is the scope_id price chain for the twap */
    twapChain: Array<number>;
}
export interface ScopeConfigurationJSON {
    /** Pubkey of the scope price feed (disabled if `null` or `default`) */
    priceFeed: string;
    /** This is the scope_id price chain that results in a price for the token */
    priceChain: Array<number>;
    /** This is the scope_id price chain for the twap */
    twapChain: Array<number>;
}
export declare class ScopeConfiguration {
    /** Pubkey of the scope price feed (disabled if `null` or `default`) */
    readonly priceFeed: Address;
    /** This is the scope_id price chain that results in a price for the token */
    readonly priceChain: Array<number>;
    /** This is the scope_id price chain for the twap */
    readonly twapChain: Array<number>;
    constructor(fields: ScopeConfigurationFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ScopeConfiguration;
    static toEncodable(fields: ScopeConfigurationFields): {
        priceFeed: Address;
        priceChain: number[];
        twapChain: number[];
    };
    toJSON(): ScopeConfigurationJSON;
    static fromJSON(obj: ScopeConfigurationJSON): ScopeConfiguration;
    toEncodable(): {
        priceFeed: Address;
        priceChain: number[];
        twapChain: number[];
    };
}
//# sourceMappingURL=ScopeConfiguration.d.ts.map