import * as types from "../types";
export interface ProgramInitParamsFields {
    stateBump: number;
}
export interface ProgramInitParamsJSON {
    stateBump: number;
}
export declare class ProgramInitParams {
    readonly stateBump: number;
    constructor(fields: ProgramInitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ProgramInitParams;
    static toEncodable(fields: ProgramInitParamsFields): {
        stateBump: number;
    };
    toJSON(): ProgramInitParamsJSON;
    static fromJSON(obj: ProgramInitParamsJSON): ProgramInitParams;
    toEncodable(): {
        stateBump: number;
    };
}
//# sourceMappingURL=ProgramInitParams.d.ts.map