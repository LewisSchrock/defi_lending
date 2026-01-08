import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface AcceptGovernanceAuthorityTransferAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare function acceptGovernanceAuthorityTransfer(accounts: AcceptGovernanceAuthorityTransferAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=acceptGovernanceAuthorityTransfer.d.ts.map