import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateIncreasePositionRequestArgs {
    params: types.UpdateIncreasePositionRequestParamsFields;
}
export interface UpdateIncreasePositionRequestAccounts {
    owner: TransactionSigner;
    perpetuals: Address;
    pool: Address;
    position: Address;
    positionRequest: Address;
    custody: Address;
    custodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<UpdateIncreasePositionRequestArgs>;
export declare function updateIncreasePositionRequest(args: UpdateIncreasePositionRequestArgs, accounts: UpdateIncreasePositionRequestAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateIncreasePositionRequest.d.ts.map