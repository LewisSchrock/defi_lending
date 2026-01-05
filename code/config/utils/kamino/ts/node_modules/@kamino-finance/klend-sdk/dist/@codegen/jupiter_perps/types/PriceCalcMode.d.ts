import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface MinJSON {
    kind: "Min";
}
export declare class Min {
    static readonly discriminator = 0;
    static readonly kind = "Min";
    readonly discriminator = 0;
    readonly kind = "Min";
    toJSON(): MinJSON;
    toEncodable(): {
        Min: {};
    };
}
export interface MaxJSON {
    kind: "Max";
}
export declare class Max {
    static readonly discriminator = 1;
    static readonly kind = "Max";
    readonly discriminator = 1;
    readonly kind = "Max";
    toJSON(): MaxJSON;
    toEncodable(): {
        Max: {};
    };
}
export interface IgnoreJSON {
    kind: "Ignore";
}
export declare class Ignore {
    static readonly discriminator = 2;
    static readonly kind = "Ignore";
    readonly discriminator = 2;
    readonly kind = "Ignore";
    toJSON(): IgnoreJSON;
    toEncodable(): {
        Ignore: {};
    };
}
export declare function fromDecoded(obj: any): types.PriceCalcModeKind;
export declare function fromJSON(obj: types.PriceCalcModeJSON): types.PriceCalcModeKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=PriceCalcMode.d.ts.map