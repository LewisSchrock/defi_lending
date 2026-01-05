import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface TokenInfoFields {
    /** UTF-8 encoded name of the token (null-terminated) */
    name: Array<number>;
    /** Heuristics limits of acceptable price */
    heuristic: types.PriceHeuristicFields;
    /** Max divergence between twap and price in bps */
    maxTwapDivergenceBps: BN;
    maxAgePriceSeconds: BN;
    maxAgeTwapSeconds: BN;
    /** Scope price configuration */
    scopeConfiguration: types.ScopeConfigurationFields;
    /** Switchboard configuration */
    switchboardConfiguration: types.SwitchboardConfigurationFields;
    /** Pyth configuration */
    pythConfiguration: types.PythConfigurationFields;
    blockPriceUsage: number;
    reserved: Array<number>;
    padding: Array<BN>;
}
export interface TokenInfoJSON {
    /** UTF-8 encoded name of the token (null-terminated) */
    name: Array<number>;
    /** Heuristics limits of acceptable price */
    heuristic: types.PriceHeuristicJSON;
    /** Max divergence between twap and price in bps */
    maxTwapDivergenceBps: string;
    maxAgePriceSeconds: string;
    maxAgeTwapSeconds: string;
    /** Scope price configuration */
    scopeConfiguration: types.ScopeConfigurationJSON;
    /** Switchboard configuration */
    switchboardConfiguration: types.SwitchboardConfigurationJSON;
    /** Pyth configuration */
    pythConfiguration: types.PythConfigurationJSON;
    blockPriceUsage: number;
    reserved: Array<number>;
    padding: Array<string>;
}
export declare class TokenInfo {
    /** UTF-8 encoded name of the token (null-terminated) */
    readonly name: Array<number>;
    /** Heuristics limits of acceptable price */
    readonly heuristic: types.PriceHeuristic;
    /** Max divergence between twap and price in bps */
    readonly maxTwapDivergenceBps: BN;
    readonly maxAgePriceSeconds: BN;
    readonly maxAgeTwapSeconds: BN;
    /** Scope price configuration */
    readonly scopeConfiguration: types.ScopeConfiguration;
    /** Switchboard configuration */
    readonly switchboardConfiguration: types.SwitchboardConfiguration;
    /** Pyth configuration */
    readonly pythConfiguration: types.PythConfiguration;
    readonly blockPriceUsage: number;
    readonly reserved: Array<number>;
    readonly padding: Array<BN>;
    constructor(fields: TokenInfoFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.TokenInfo;
    static toEncodable(fields: TokenInfoFields): {
        name: number[];
        heuristic: {
            lower: BN;
            upper: BN;
            exp: BN;
        };
        maxTwapDivergenceBps: BN;
        maxAgePriceSeconds: BN;
        maxAgeTwapSeconds: BN;
        scopeConfiguration: {
            priceFeed: Address;
            priceChain: number[];
            twapChain: number[];
        };
        switchboardConfiguration: {
            priceAggregator: Address;
            twapAggregator: Address;
        };
        pythConfiguration: {
            price: Address;
        };
        blockPriceUsage: number;
        reserved: number[];
        padding: BN[];
    };
    toJSON(): TokenInfoJSON;
    static fromJSON(obj: TokenInfoJSON): TokenInfo;
    toEncodable(): {
        name: number[];
        heuristic: {
            lower: BN;
            upper: BN;
            exp: BN;
        };
        maxTwapDivergenceBps: BN;
        maxAgePriceSeconds: BN;
        maxAgeTwapSeconds: BN;
        scopeConfiguration: {
            priceFeed: Address;
            priceChain: number[];
            twapChain: number[];
        };
        switchboardConfiguration: {
            priceAggregator: Address;
            twapAggregator: Address;
        };
        pythConfiguration: {
            price: Address;
        };
        blockPriceUsage: number;
        reserved: number[];
        padding: BN[];
    };
}
//# sourceMappingURL=TokenInfo.d.ts.map