import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface AggregatorOpenRoundArgs {
    params: types.AggregatorOpenRoundParamsFields;
}
export interface AggregatorOpenRoundAccounts {
    aggregator: Address;
    lease: Address;
    oracleQueue: Address;
    queueAuthority: Address;
    permission: Address;
    escrow: Address;
    programState: Address;
    payoutWallet: Address;
    tokenProgram: Address;
    dataBuffer: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorOpenRound(args: AggregatorOpenRoundArgs, accounts: AggregatorOpenRoundAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorOpenRound.d.ts.map