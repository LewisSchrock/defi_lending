import * as types from "../types";
import * as borsh from "@coral-xyz/borsh";
export interface PendingAdminJSON {
    kind: "PendingAdmin";
}
export declare class PendingAdmin {
    static readonly discriminator = 0;
    static readonly kind = "PendingAdmin";
    readonly discriminator = 0;
    readonly kind = "PendingAdmin";
    toJSON(): PendingAdminJSON;
    toEncodable(): {
        PendingAdmin: {};
    };
}
export interface FeeCollectorJSON {
    kind: "FeeCollector";
}
export declare class FeeCollector {
    static readonly discriminator = 1;
    static readonly kind = "FeeCollector";
    readonly discriminator = 1;
    readonly kind = "FeeCollector";
    toJSON(): FeeCollectorJSON;
    toEncodable(): {
        FeeCollector: {};
    };
}
export declare function fromDecoded(obj: any): types.UpdateGlobalConfigModeKind;
export declare function fromJSON(obj: types.UpdateGlobalConfigModeJSON): types.UpdateGlobalConfigModeKind;
export declare function layout(property?: string): borsh.EnumLayout<unknown>;
//# sourceMappingURL=UpdateGlobalConfigMode.d.ts.map