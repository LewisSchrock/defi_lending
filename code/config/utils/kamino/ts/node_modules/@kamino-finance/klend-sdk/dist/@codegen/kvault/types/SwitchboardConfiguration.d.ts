import { Address } from "@solana/kit";
import * as types from "../types";
export interface SwitchboardConfigurationFields {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    priceAggregator: Address;
    twapAggregator: Address;
}
export interface SwitchboardConfigurationJSON {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    priceAggregator: string;
    twapAggregator: string;
}
export declare class SwitchboardConfiguration {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    readonly priceAggregator: Address;
    readonly twapAggregator: Address;
    constructor(fields: SwitchboardConfigurationFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SwitchboardConfiguration;
    static toEncodable(fields: SwitchboardConfigurationFields): {
        priceAggregator: Address;
        twapAggregator: Address;
    };
    toJSON(): SwitchboardConfigurationJSON;
    static fromJSON(obj: SwitchboardConfigurationJSON): SwitchboardConfiguration;
    toEncodable(): {
        priceAggregator: Address;
        twapAggregator: Address;
    };
}
//# sourceMappingURL=SwitchboardConfiguration.d.ts.map