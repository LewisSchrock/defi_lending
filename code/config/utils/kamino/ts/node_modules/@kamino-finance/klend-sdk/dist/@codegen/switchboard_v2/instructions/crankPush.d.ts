import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface CrankPushArgs {
    params: types.CrankPushParamsFields;
}
export interface CrankPushAccounts {
    crank: Address;
    aggregator: Address;
    oracleQueue: Address;
    queueAuthority: Address;
    permission: Address;
    lease: Address;
    escrow: Address;
    programState: Address;
    dataBuffer: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function crankPush(args: CrankPushArgs, accounts: CrankPushAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=crankPush.d.ts.map