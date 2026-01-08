import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RefreshObligationFarmsForReserveArgs {
    mode: number;
}
export interface RefreshObligationFarmsForReserveAccounts {
    crank: TransactionSigner;
    baseAccounts: {
        obligation: Address;
        lendingMarketAuthority: Address;
        reserve: Address;
        reserveFarmState: Address;
        obligationFarmUserState: Address;
        lendingMarket: Address;
    };
    farmsProgram: Address;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<RefreshObligationFarmsForReserveArgs>;
export declare function refreshObligationFarmsForReserve(args: RefreshObligationFarmsForReserveArgs, accounts: RefreshObligationFarmsForReserveAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=refreshObligationFarmsForReserve.d.ts.map