import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSetAuthorityArgs {
    params: types.AggregatorSetAuthorityParamsFields;
}
export interface AggregatorSetAuthorityAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    newAuthority: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSetAuthority(args: AggregatorSetAuthorityArgs, accounts: AggregatorSetAuthorityAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSetAuthority.d.ts.map