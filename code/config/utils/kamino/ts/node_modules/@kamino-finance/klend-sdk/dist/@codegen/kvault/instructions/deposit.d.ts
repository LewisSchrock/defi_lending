import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositArgs {
    maxAmount: BN;
}
export interface DepositAccounts {
    user: TransactionSigner;
    vaultState: Address;
    tokenVault: Address;
    tokenMint: Address;
    baseVaultAuthority: Address;
    sharesMint: Address;
    userTokenAta: Address;
    userSharesAta: Address;
    klendProgram: Address;
    tokenProgram: Address;
    sharesTokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositArgs>;
export declare function deposit(args: DepositArgs, accounts: DepositAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=deposit.d.ts.map