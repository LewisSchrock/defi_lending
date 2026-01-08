import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export type PartialFields = {
    numSignatures: number;
};
export type PartialValue = {
    numSignatures: number;
};
export interface PartialJSON {
    kind: "Partial";
    value: {
        numSignatures: number;
    };
}
export declare class Partial {
    static readonly discriminator = 0;
    static readonly kind = "Partial";
    readonly discriminator = 0;
    readonly kind = "Partial";
    readonly value: PartialValue;
    constructor(value: PartialFields);
    toJSON(): PartialJSON;
    toEncodable(): {
        Partial: {
            numSignatures: number;
        };
    };
}
export interface FullJSON {
    kind: "Full";
}
export declare class Full {
    static readonly discriminator = 1;
    static readonly kind = "Full";
    readonly discriminator = 1;
    readonly kind = "Full";
    toJSON(): FullJSON;
    toEncodable(): {
        Full: {};
    };
}
export declare function fromDecoded(obj: any): types.VerificationLevelKind;
export declare function fromJSON(obj: types.VerificationLevelJSON): types.VerificationLevelKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=VerificationLevel.d.ts.map