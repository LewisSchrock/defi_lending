import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetObligationOrderArgs {
    index: number;
    order: types.ObligationOrderFields;
}
export interface SetObligationOrderAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
}
export declare const layout: import("buffer-layout").Layout<SetObligationOrderArgs>;
export declare function setObligationOrder(args: SetObligationOrderArgs, accounts: SetObligationOrderAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setObligationOrder.d.ts.map