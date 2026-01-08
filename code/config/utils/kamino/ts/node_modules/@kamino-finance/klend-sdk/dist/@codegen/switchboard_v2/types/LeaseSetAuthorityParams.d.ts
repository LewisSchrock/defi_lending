import * as types from "../types";
export interface LeaseSetAuthorityParamsFields {
}
export interface LeaseSetAuthorityParamsJSON {
}
export declare class LeaseSetAuthorityParams {
    constructor(fields: LeaseSetAuthorityParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LeaseSetAuthorityParams;
    static toEncodable(fields: LeaseSetAuthorityParamsFields): {};
    toJSON(): LeaseSetAuthorityParamsJSON;
    static fromJSON(obj: LeaseSetAuthorityParamsJSON): LeaseSetAuthorityParams;
    toEncodable(): {};
}
//# sourceMappingURL=LeaseSetAuthorityParams.d.ts.map