import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface AddLiquidityArgs {
    params: types.AddLiquidityParamsFields;
}
export interface AddLiquidityAccounts {
    owner: TransactionSigner;
    fundingAccount: Address;
    lpTokenAccount: Address;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyOracleAccount: Address;
    custodyTokenAccount: Address;
    lpTokenMint: Address;
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<AddLiquidityArgs>;
export declare function addLiquidity(args: AddLiquidityArgs, accounts: AddLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=addLiquidity.d.ts.map