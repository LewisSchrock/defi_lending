import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RemoveLiquidityArgs {
    params: types.RemoveLiquidityParamsFields;
}
export interface RemoveLiquidityAccounts {
    owner: TransactionSigner;
    receivingAccount: Address;
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
export declare const layout: import("buffer-layout").Layout<RemoveLiquidityArgs>;
export declare function removeLiquidity(args: RemoveLiquidityArgs, accounts: RemoveLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=removeLiquidity.d.ts.map