import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface ClosePositionRequestArgs {
    params: types.ClosePositionRequestParamsFields;
}
export interface ClosePositionRequestAccounts {
    keeper: Option<TransactionSigner>;
    owner: Address;
    ownerAta: Option<Address>;
    pool: Address;
    positionRequest: Address;
    positionRequestAta: Address;
    position: Address;
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<ClosePositionRequestArgs>;
export declare function closePositionRequest(args: ClosePositionRequestArgs, accounts: ClosePositionRequestAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=closePositionRequest.d.ts.map