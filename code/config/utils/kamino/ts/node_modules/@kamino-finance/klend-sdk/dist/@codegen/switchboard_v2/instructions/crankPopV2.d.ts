import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface CrankPopV2Args {
    params: types.CrankPopParamsV2Fields;
}
export interface CrankPopV2Accounts {
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
export declare function crankPopV2(args: CrankPopV2Args, accounts: CrankPopV2Accounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=crankPopV2.d.ts.map