import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitLendingMarketArgs {
    quoteCurrency: Array<number>;
}
export interface InitLendingMarketAccounts {
    lendingMarketOwner: TransactionSigner;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    systemProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<InitLendingMarketArgs>;
export declare function initLendingMarket(args: InitLendingMarketArgs, accounts: InitLendingMarketAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initLendingMarket.d.ts.map