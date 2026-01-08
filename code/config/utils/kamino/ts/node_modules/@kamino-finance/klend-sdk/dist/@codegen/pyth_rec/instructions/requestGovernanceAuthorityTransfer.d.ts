import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RequestGovernanceAuthorityTransferArgs {
    targetGovernanceAuthority: Address;
}
export interface RequestGovernanceAuthorityTransferAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare const layout: import("buffer-layout").Layout<RequestGovernanceAuthorityTransferArgs>;
export declare function requestGovernanceAuthorityTransfer(args: RequestGovernanceAuthorityTransferArgs, accounts: RequestGovernanceAuthorityTransferAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=requestGovernanceAuthorityTransfer.d.ts.map