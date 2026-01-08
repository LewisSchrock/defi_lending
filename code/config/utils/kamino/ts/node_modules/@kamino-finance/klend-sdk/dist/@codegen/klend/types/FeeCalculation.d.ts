import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface ExclusiveJSON {
    kind: "Exclusive";
}
export declare class Exclusive {
    static readonly discriminator = 0;
    static readonly kind = "Exclusive";
    readonly discriminator = 0;
    readonly kind = "Exclusive";
    toJSON(): ExclusiveJSON;
    toEncodable(): {
        Exclusive: {};
    };
}
export interface InclusiveJSON {
    kind: "Inclusive";
}
export declare class Inclusive {
    static readonly discriminator = 1;
    static readonly kind = "Inclusive";
    readonly discriminator = 1;
    readonly kind = "Inclusive";
    toJSON(): InclusiveJSON;
    toEncodable(): {
        Inclusive: {};
    };
}
export declare function fromDecoded(obj: any): types.FeeCalculationKind;
export declare function fromJSON(obj: types.FeeCalculationJSON): types.FeeCalculationKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=FeeCalculation.d.ts.map