import * as types from "../types";
export interface WithdrawFeesParamsFields {
}
export interface WithdrawFeesParamsJSON {
}
export declare class WithdrawFeesParams {
    constructor(fields: WithdrawFeesParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.WithdrawFeesParams;
    static toEncodable(fields: WithdrawFeesParamsFields): {};
    toJSON(): WithdrawFeesParamsJSON;
    static fromJSON(obj: WithdrawFeesParamsJSON): WithdrawFeesParams;
    toEncodable(): {};
}
//# sourceMappingURL=WithdrawFeesParams.d.ts.map