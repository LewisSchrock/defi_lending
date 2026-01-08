import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface MarketJSON {
    kind: "Market";
}
export declare class Market {
    static readonly discriminator = 0;
    static readonly kind = "Market";
    readonly discriminator = 0;
    readonly kind = "Market";
    toJSON(): MarketJSON;
    toEncodable(): {
        Market: {};
    };
}
export interface TriggerJSON {
    kind: "Trigger";
}
export declare class Trigger {
    static readonly discriminator = 1;
    static readonly kind = "Trigger";
    readonly discriminator = 1;
    readonly kind = "Trigger";
    toJSON(): TriggerJSON;
    toEncodable(): {
        Trigger: {};
    };
}
export declare function fromDecoded(obj: any): types.RequestTypeKind;
export declare function fromJSON(obj: types.RequestTypeJSON): types.RequestTypeKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=RequestType.d.ts.map