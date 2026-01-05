import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SwapExactOutArgs {
    params: types.SwapExactOutParamsFields;
}
export interface SwapExactOutAccounts {
    owner: TransactionSigner;
    fundingAccount: Address;
    receivingAccount: Address;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    receivingCustody: Address;
    receivingCustodyOracleAccount: Address;
    receivingCustodyTokenAccount: Address;
    dispensingCustody: Address;
    dispensingCustodyOracleAccount: Address;
    dispensingCustodyTokenAccount: Address;
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<SwapExactOutArgs>;
export declare function swapExactOut(args: SwapExactOutArgs, accounts: SwapExactOutAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=swapExactOut.d.ts.map