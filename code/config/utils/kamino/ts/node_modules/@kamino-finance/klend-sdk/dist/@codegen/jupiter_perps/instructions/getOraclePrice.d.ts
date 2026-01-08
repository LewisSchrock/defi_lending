import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetOraclePriceAccounts {
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyOracleAccount: Address;
}
export declare function getOraclePrice(accounts: GetOraclePriceAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getOraclePrice.d.ts.map