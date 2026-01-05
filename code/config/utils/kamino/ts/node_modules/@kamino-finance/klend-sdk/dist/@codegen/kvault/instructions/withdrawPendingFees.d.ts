import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawPendingFeesAccounts {
    vaultAdminAuthority: TransactionSigner;
    vaultState: Address;
    reserve: Address;
    tokenVault: Address;
    ctokenVault: Address;
    baseVaultAuthority: Address;
    tokenAta: Address;
    tokenMint: Address;
    /** CPI accounts */
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    reserveLiquiditySupply: Address;
    reserveCollateralMint: Address;
    klendProgram: Address;
    tokenProgram: Address;
    reserveCollateralTokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare function withdrawPendingFees(accounts: WithdrawPendingFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawPendingFees.d.ts.map