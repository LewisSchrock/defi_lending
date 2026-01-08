import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateDecreasePositionRequestArgs {
    params: types.UpdateDecreasePositionRequestParamsFields;
}
export interface UpdateDecreasePositionRequestAccounts {
    owner: TransactionSigner;
    perpetuals: Address;
    pool: Address;
    position: Address;
    positionRequest: Address;
    custody: Address;
    custodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<UpdateDecreasePositionRequestArgs>;
export declare function updateDecreasePositionRequest(args: UpdateDecreasePositionRequestArgs, accounts: UpdateDecreasePositionRequestAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateDecreasePositionRequest.d.ts.map