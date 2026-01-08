import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetMinimumSignaturesArgs {
    minimumSignatures: number;
}
export interface SetMinimumSignaturesAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare const layout: import("buffer-layout").Layout<SetMinimumSignaturesArgs>;
export declare function setMinimumSignatures(args: SetMinimumSignaturesArgs, accounts: SetMinimumSignaturesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setMinimumSignatures.d.ts.map