import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface ActiveJSON {
    kind: "Active";
}
export declare class Active {
    static readonly discriminator = 0;
    static readonly kind = "Active";
    readonly discriminator = 0;
    readonly kind = "Active";
    toJSON(): ActiveJSON;
    toEncodable(): {
        Active: {};
    };
}
export interface ObsoleteJSON {
    kind: "Obsolete";
}
export declare class Obsolete {
    static readonly discriminator = 1;
    static readonly kind = "Obsolete";
    readonly discriminator = 1;
    readonly kind = "Obsolete";
    toJSON(): ObsoleteJSON;
    toEncodable(): {
        Obsolete: {};
    };
}
export interface HiddenJSON {
    kind: "Hidden";
}
export declare class Hidden {
    static readonly discriminator = 2;
    static readonly kind = "Hidden";
    readonly discriminator = 2;
    readonly kind = "Hidden";
    toJSON(): HiddenJSON;
    toEncodable(): {
        Hidden: {};
    };
}
export declare function fromDecoded(obj: any): types.ReserveStatusKind;
export declare function fromJSON(obj: types.ReserveStatusJSON): types.ReserveStatusKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=ReserveStatus.d.ts.map