import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitObligationArgs {
    args: types.InitObligationArgsFields;
}
export interface InitObligationAccounts {
    obligationOwner: TransactionSigner;
    feePayer: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    seed1Account: Address;
    seed2Account: Address;
    ownerUserMetadata: Address;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitObligationArgs>;
export declare function initObligation(args: InitObligationArgs, accounts: InitObligationAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initObligation.d.ts.map