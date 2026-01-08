import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface NoneJSON {
    kind: "None";
}
export declare class None {
    static readonly discriminator = 0;
    static readonly kind = "None";
    readonly discriminator = 0;
    readonly kind = "None";
    toJSON(): NoneJSON;
    toEncodable(): {
        None: {};
    };
}
export interface LongJSON {
    kind: "Long";
}
export declare class Long {
    static readonly discriminator = 1;
    static readonly kind = "Long";
    readonly discriminator = 1;
    readonly kind = "Long";
    toJSON(): LongJSON;
    toEncodable(): {
        Long: {};
    };
}
export interface ShortJSON {
    kind: "Short";
}
export declare class Short {
    static readonly discriminator = 2;
    static readonly kind = "Short";
    readonly discriminator = 2;
    readonly kind = "Short";
    toJSON(): ShortJSON;
    toEncodable(): {
        Short: {};
    };
}
export declare function fromDecoded(obj: any): types.SideKind;
export declare function fromJSON(obj: types.SideJSON): types.SideKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=Side.d.ts.map