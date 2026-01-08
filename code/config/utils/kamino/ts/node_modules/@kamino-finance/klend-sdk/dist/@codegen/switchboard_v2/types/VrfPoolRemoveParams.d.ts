import * as types from "../types";
export interface VrfPoolRemoveParamsFields {
}
export interface VrfPoolRemoveParamsJSON {
}
export declare class VrfPoolRemoveParams {
    constructor(fields: VrfPoolRemoveParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfPoolRemoveParams;
    static toEncodable(fields: VrfPoolRemoveParamsFields): {};
    toJSON(): VrfPoolRemoveParamsJSON;
    static fromJSON(obj: VrfPoolRemoveParamsJSON): VrfPoolRemoveParams;
    toEncodable(): {};
}
//# sourceMappingURL=VrfPoolRemoveParams.d.ts.map