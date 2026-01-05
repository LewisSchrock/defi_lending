import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateReserveConfigArgs {
    mode: types.UpdateConfigModeKind;
    value: Uint8Array;
    skipConfigIntegrityValidation: boolean;
}
export interface UpdateReserveConfigAccounts {
    signer: TransactionSigner;
    globalConfig: Address;
    lendingMarket: Address;
    reserve: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function updateReserveConfig(args: UpdateReserveConfigArgs, accounts: UpdateReserveConfigAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateReserveConfig.d.ts.map