import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawFeesArgs {
    params: types.WithdrawFeesParamsFields;
}
export interface WithdrawFeesAccounts {
    keeper: TransactionSigner;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyTokenAccount: Address;
    custodyOracleAccount: Address;
    receivingTokenAccount: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawFeesArgs>;
export declare function withdrawFees(args: WithdrawFeesArgs, accounts: WithdrawFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawFees.d.ts.map