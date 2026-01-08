import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export type BoolFields = [boolean];
export type BoolValue = [boolean];
export interface BoolJSON {
    kind: "Bool";
    value: [boolean];
}
export declare class Bool {
    static readonly discriminator = 0;
    static readonly kind = "Bool";
    readonly discriminator = 0;
    readonly kind = "Bool";
    readonly value: BoolValue;
    constructor(value: BoolFields);
    toJSON(): BoolJSON;
    toEncodable(): {
        Bool: {
            _0: boolean;
        };
    };
}
export type U8Fields = [number];
export type U8Value = [number];
export interface U8JSON {
    kind: "U8";
    value: [number];
}
export declare class U8 {
    static readonly discriminator = 1;
    static readonly kind = "U8";
    readonly discriminator = 1;
    readonly kind = "U8";
    readonly value: U8Value;
    constructor(value: U8Fields);
    toJSON(): U8JSON;
    toEncodable(): {
        U8: {
            _0: number;
        };
    };
}
export type U8ArrayFields = [Array<number>];
export type U8ArrayValue = [Array<number>];
export interface U8ArrayJSON {
    kind: "U8Array";
    value: [Array<number>];
}
export declare class U8Array {
    static readonly discriminator = 2;
    static readonly kind = "U8Array";
    readonly discriminator = 2;
    readonly kind = "U8Array";
    readonly value: U8ArrayValue;
    constructor(value: U8ArrayFields);
    toJSON(): U8ArrayJSON;
    toEncodable(): {
        U8Array: {
            _0: number[];
        };
    };
}
export type U16Fields = [number];
export type U16Value = [number];
export interface U16JSON {
    kind: "U16";
    value: [number];
}
export declare class U16 {
    static readonly discriminator = 3;
    static readonly kind = "U16";
    readonly discriminator = 3;
    readonly kind = "U16";
    readonly value: U16Value;
    constructor(value: U16Fields);
    toJSON(): U16JSON;
    toEncodable(): {
        U16: {
            _0: number;
        };
    };
}
export type U64Fields = [BN];
export type U64Value = [BN];
export interface U64JSON {
    kind: "U64";
    value: [string];
}
export declare class U64 {
    static readonly discriminator = 4;
    static readonly kind = "U64";
    readonly discriminator = 4;
    readonly kind = "U64";
    readonly value: U64Value;
    constructor(value: U64Fields);
    toJSON(): U64JSON;
    toEncodable(): {
        U64: {
            _0: BN;
        };
    };
}
export type U128Fields = [BN];
export type U128Value = [BN];
export interface U128JSON {
    kind: "U128";
    value: [string];
}
export declare class U128 {
    static readonly discriminator = 5;
    static readonly kind = "U128";
    readonly discriminator = 5;
    readonly kind = "U128";
    readonly value: U128Value;
    constructor(value: U128Fields);
    toJSON(): U128JSON;
    toEncodable(): {
        U128: {
            _0: BN;
        };
    };
}
export type PubkeyFields = [Address];
export type PubkeyValue = [Address];
export interface PubkeyJSON {
    kind: "Pubkey";
    value: [string];
}
export declare class Pubkey {
    static readonly discriminator = 6;
    static readonly kind = "Pubkey";
    readonly discriminator = 6;
    readonly kind = "Pubkey";
    readonly value: PubkeyValue;
    constructor(value: PubkeyFields);
    toJSON(): PubkeyJSON;
    toEncodable(): {
        Pubkey: {
            _0: Address;
        };
    };
}
export type ElevationGroupFields = [types.ElevationGroupFields];
export type ElevationGroupValue = [types.ElevationGroup];
export interface ElevationGroupJSON {
    kind: "ElevationGroup";
    value: [types.ElevationGroupJSON];
}
export declare class ElevationGroup {
    static readonly discriminator = 7;
    static readonly kind = "ElevationGroup";
    readonly discriminator = 7;
    readonly kind = "ElevationGroup";
    readonly value: ElevationGroupValue;
    constructor(value: ElevationGroupFields);
    toJSON(): ElevationGroupJSON;
    toEncodable(): {
        ElevationGroup: {
            _0: {
                maxLiquidationBonusBps: number;
                id: number;
                ltvPct: number;
                liquidationThresholdPct: number;
                allowNewLoans: number;
                maxReservesAsCollateral: number;
                padding0: number;
                debtReserve: Address;
                padding1: BN[];
            };
        };
    };
}
export type NameFields = [Array<number>];
export type NameValue = [Array<number>];
export interface NameJSON {
    kind: "Name";
    value: [Array<number>];
}
export declare class Name {
    static readonly discriminator = 8;
    static readonly kind = "Name";
    readonly discriminator = 8;
    readonly kind = "Name";
    readonly value: NameValue;
    constructor(value: NameFields);
    toJSON(): NameJSON;
    toEncodable(): {
        Name: {
            _0: number[];
        };
    };
}
export declare function fromDecoded(obj: any): types.UpdateLendingMarketConfigValueKind;
export declare function fromJSON(obj: types.UpdateLendingMarketConfigValueJSON): types.UpdateLendingMarketConfigValueKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=UpdateLendingMarketConfigValue.d.ts.map