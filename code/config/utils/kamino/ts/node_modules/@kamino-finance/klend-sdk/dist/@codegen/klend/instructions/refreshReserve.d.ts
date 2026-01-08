import { Address, AccountMeta, AccountSignerMeta, Instruction, Option } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RefreshReserveAccounts {
    reserve: Address;
    lendingMarket: Address;
    pythOracle: Option<Address>;
    switchboardPriceOracle: Option<Address>;
    switchboardTwapOracle: Option<Address>;
    scopePrices: Option<Address>;
}
export declare function refreshReserve(accounts: RefreshReserveAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=refreshReserve.d.ts.map