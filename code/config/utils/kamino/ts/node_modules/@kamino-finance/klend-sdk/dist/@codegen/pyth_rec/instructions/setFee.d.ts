import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetFeeArgs {
    singleUpdateFeeInLamports: BN;
}
export interface SetFeeAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare const layout: import("buffer-layout").Layout<SetFeeArgs>;
export declare function setFee(args: SetFeeArgs, accounts: SetFeeAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setFee.d.ts.map