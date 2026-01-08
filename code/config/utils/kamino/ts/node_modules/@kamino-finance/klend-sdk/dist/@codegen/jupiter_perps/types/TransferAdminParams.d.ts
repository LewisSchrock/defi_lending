import * as types from "../types";
export interface TransferAdminParamsFields {
}
export interface TransferAdminParamsJSON {
}
export declare class TransferAdminParams {
    constructor(fields: TransferAdminParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.TransferAdminParams;
    static toEncodable(fields: TransferAdminParamsFields): {};
    toJSON(): TransferAdminParamsJSON;
    static fromJSON(obj: TransferAdminParamsJSON): TransferAdminParams;
    toEncodable(): {};
}
//# sourceMappingURL=TransferAdminParams.d.ts.map