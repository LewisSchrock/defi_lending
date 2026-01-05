import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitFarmsForReserveArgs {
    mode: number;
}
export interface InitFarmsForReserveAccounts {
    lendingMarketOwner: TransactionSigner;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    reserve: Address;
    farmsProgram: Address;
    farmsGlobalConfig: Address;
    farmState: Address;
    farmsVaultAuthority: Address;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitFarmsForReserveArgs>;
export declare function initFarmsForReserve(args: InitFarmsForReserveArgs, accounts: InitFarmsForReserveAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initFarmsForReserve.d.ts.map