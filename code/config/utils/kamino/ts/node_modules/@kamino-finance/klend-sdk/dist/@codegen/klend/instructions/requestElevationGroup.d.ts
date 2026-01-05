import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RequestElevationGroupArgs {
    elevationGroup: number;
}
export interface RequestElevationGroupAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
}
export declare const layout: import("buffer-layout").Layout<RequestElevationGroupArgs>;
export declare function requestElevationGroup(args: RequestElevationGroupArgs, accounts: RequestElevationGroupAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=requestElevationGroup.d.ts.map