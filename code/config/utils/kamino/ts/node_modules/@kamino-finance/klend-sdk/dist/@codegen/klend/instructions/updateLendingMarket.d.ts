import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateLendingMarketArgs {
    mode: BN;
    value: Array<number>;
}
export interface UpdateLendingMarketAccounts {
    lendingMarketOwner: TransactionSigner;
    lendingMarket: Address;
}
export declare const layout: import("buffer-layout").Layout<UpdateLendingMarketArgs>;
export declare function updateLendingMarket(args: UpdateLendingMarketArgs, accounts: UpdateLendingMarketAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateLendingMarket.d.ts.map