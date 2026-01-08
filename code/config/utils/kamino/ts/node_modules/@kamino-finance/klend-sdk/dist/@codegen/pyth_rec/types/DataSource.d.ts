import { Address } from "@solana/kit";
import * as types from "../types";
export interface DataSourceFields {
    chain: number;
    emitter: Address;
}
export interface DataSourceJSON {
    chain: number;
    emitter: string;
}
export declare class DataSource {
    readonly chain: number;
    readonly emitter: Address;
    constructor(fields: DataSourceFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.DataSource;
    static toEncodable(fields: DataSourceFields): {
        chain: number;
        emitter: Address;
    };
    toJSON(): DataSourceJSON;
    static fromJSON(obj: DataSourceJSON): DataSource;
    toEncodable(): {
        chain: number;
        emitter: Address;
    };
}
//# sourceMappingURL=DataSource.d.ts.map