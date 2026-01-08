import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GiveUpPendingFeesArgs {
    maxAmountToGiveUp: BN;
}
export interface GiveUpPendingFeesAccounts {
    vaultAdminAuthority: TransactionSigner;
    vaultState: Address;
    klendProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<GiveUpPendingFeesArgs>;
export declare function giveUpPendingFees(args: GiveUpPendingFeesArgs, accounts: GiveUpPendingFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=giveUpPendingFees.d.ts.map