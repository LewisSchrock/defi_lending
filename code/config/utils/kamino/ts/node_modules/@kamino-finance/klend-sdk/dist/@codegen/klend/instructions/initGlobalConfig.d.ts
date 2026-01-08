import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitGlobalConfigAccounts {
    payer: TransactionSigner;
    globalConfig: Address;
    programData: Address;
    systemProgram: Address;
    rent: Address;
}
export declare function initGlobalConfig(accounts: InitGlobalConfigAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initGlobalConfig.d.ts.map