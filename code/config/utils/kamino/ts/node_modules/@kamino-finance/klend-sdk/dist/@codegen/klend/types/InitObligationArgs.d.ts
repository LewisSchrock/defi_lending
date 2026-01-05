import * as types from "../types";
export interface InitObligationArgsFields {
    tag: number;
    id: number;
}
export interface InitObligationArgsJSON {
    tag: number;
    id: number;
}
export declare class InitObligationArgs {
    readonly tag: number;
    readonly id: number;
    constructor(fields: InitObligationArgsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.InitObligationArgs;
    static toEncodable(fields: InitObligationArgsFields): {
        tag: number;
        id: number;
    };
    toJSON(): InitObligationArgsJSON;
    static fromJSON(obj: InitObligationArgsJSON): InitObligationArgs;
    toEncodable(): {
        tag: number;
        id: number;
    };
}
//# sourceMappingURL=InitObligationArgs.d.ts.map