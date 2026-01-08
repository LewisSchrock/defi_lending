import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RefreshReservesBatchArgs {
    skipPriceUpdates: boolean;
}
export declare const layout: import("buffer-layout").Layout<RefreshReservesBatchArgs>;
export declare function refreshReservesBatch(args: RefreshReservesBatchArgs, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=refreshReservesBatch.d.ts.map