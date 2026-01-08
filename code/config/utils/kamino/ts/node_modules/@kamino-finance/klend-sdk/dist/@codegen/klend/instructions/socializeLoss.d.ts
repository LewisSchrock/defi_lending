import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SocializeLossArgs {
    liquidityAmount: BN;
}
export interface SocializeLossAccounts {
    riskCouncil: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    reserve: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<SocializeLossArgs>;
export declare function socializeLoss(args: SocializeLossArgs, accounts: SocializeLossAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=socializeLoss.d.ts.map