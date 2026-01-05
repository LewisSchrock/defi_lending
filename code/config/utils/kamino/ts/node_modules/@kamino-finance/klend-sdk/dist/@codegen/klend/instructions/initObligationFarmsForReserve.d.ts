import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitObligationFarmsForReserveArgs {
    mode: number;
}
export interface InitObligationFarmsForReserveAccounts {
    payer: TransactionSigner;
    owner: Address;
    obligation: Address;
    lendingMarketAuthority: Address;
    reserve: Address;
    reserveFarmState: Address;
    obligationFarm: Address;
    lendingMarket: Address;
    farmsProgram: Address;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitObligationFarmsForReserveArgs>;
export declare function initObligationFarmsForReserve(args: InitObligationFarmsForReserveArgs, accounts: InitObligationFarmsForReserveAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initObligationFarmsForReserve.d.ts.map