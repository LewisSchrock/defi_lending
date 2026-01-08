import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface CollateralJSON {
    kind: "Collateral";
}
export declare class Collateral {
    static readonly discriminator = 0;
    static readonly kind = "Collateral";
    readonly discriminator = 0;
    readonly kind = "Collateral";
    toJSON(): CollateralJSON;
    toEncodable(): {
        Collateral: {};
    };
}
export interface DebtJSON {
    kind: "Debt";
}
export declare class Debt {
    static readonly discriminator = 1;
    static readonly kind = "Debt";
    readonly discriminator = 1;
    readonly kind = "Debt";
    toJSON(): DebtJSON;
    toEncodable(): {
        Debt: {};
    };
}
export declare function fromDecoded(obj: any): types.ReserveFarmKindKind;
export declare function fromJSON(obj: types.ReserveFarmKindJSON): types.ReserveFarmKindKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=ReserveFarmKind.d.ts.map