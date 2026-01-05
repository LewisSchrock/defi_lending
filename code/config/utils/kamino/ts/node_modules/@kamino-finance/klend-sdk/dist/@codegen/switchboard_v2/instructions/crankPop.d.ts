import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface CrankPopArgs {
    params: types.CrankPopParamsFields;
}
export interface CrankPopAccounts {
    crank: Address;
    oracleQueue: Address;
    queueAuthority: Address;
    programState: Address;
    payoutWallet: Address;
    tokenProgram: Address;
    crankDataBuffer: Address;
    queueDataBuffer: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function crankPop(args: CrankPopArgs, accounts: CrankPopAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=crankPop.d.ts.map