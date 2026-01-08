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
export interface TestJSON {
    kind: "Test";
}
export declare class Test {
    static readonly discriminator = 1;
    static readonly kind = "Test";
    readonly discriminator = 1;
    readonly kind = "Test";
    toJSON(): TestJSON;
    toEncodable(): {
        Test: {};
    };
}
export interface PythJSON {
    kind: "Pyth";
}
export declare class Pyth {
    static readonly discriminator = 2;
    static readonly kind = "Pyth";
    readonly discriminator = 2;
    readonly kind = "Pyth";
    toJSON(): PythJSON;
    toEncodable(): {
        Pyth: {};
    };
}
export declare function fromDecoded(obj: any): types.OracleTypeKind;
export declare function fromJSON(obj: types.OracleTypeJSON): types.OracleTypeKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=OracleType.d.ts.map