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
export interface IncreaseJSON {
    kind: "Increase";
}
export declare class Increase {
    static readonly discriminator = 1;
    static readonly kind = "Increase";
    readonly discriminator = 1;
    readonly kind = "Increase";
    toJSON(): IncreaseJSON;
    toEncodable(): {
        Increase: {};
    };
}
export interface DecreaseJSON {
    kind: "Decrease";
}
export declare class Decrease {
    static readonly discriminator = 2;
    static readonly kind = "Decrease";
    readonly discriminator = 2;
    readonly kind = "Decrease";
    toJSON(): DecreaseJSON;
    toEncodable(): {
        Decrease: {};
    };
}
export declare function fromDecoded(obj: any): types.RequestChangeKind;
export declare function fromJSON(obj: types.RequestChangeJSON): types.RequestChangeKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=RequestChange.d.ts.map