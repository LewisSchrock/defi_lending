import BN from "bn.js";
import * as types from "../types";
export interface SwitchboardDecimalFields {
    mantissa: BN;
    scale: number;
}
export interface SwitchboardDecimalJSON {
    mantissa: string;
    scale: number;
}
export declare class SwitchboardDecimal {
    readonly mantissa: BN;
    readonly scale: number;
    constructor(fields: SwitchboardDecimalFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SwitchboardDecimal;
    static toEncodable(fields: SwitchboardDecimalFields): {
        mantissa: BN;
        scale: number;
    };
    toJSON(): SwitchboardDecimalJSON;
    static fromJSON(obj: SwitchboardDecimalJSON): SwitchboardDecimal;
    toEncodable(): {
        mantissa: BN;
        scale: number;
    };
}
//# sourceMappingURL=SwitchboardDecimal.d.ts.map