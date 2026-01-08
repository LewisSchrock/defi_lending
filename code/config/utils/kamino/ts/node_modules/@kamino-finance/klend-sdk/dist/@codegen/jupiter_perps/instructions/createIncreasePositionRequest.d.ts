import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface CreateIncreasePositionRequestArgs {
    params: types.CreateIncreasePositionRequestParamsFields;
}
export interface CreateIncreasePositionRequestAccounts {
    owner: TransactionSigner;
    fundingAccount: Address;
    perpetuals: Address;
    pool: Address;
    position: Address;
    positionRequest: Address;
    positionRequestAta: Address;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
    inputMint: Address;
    referral: Option<Address>;
    tokenProgram: Address;
    associatedTokenProgram: Address;
    systemProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function createIncreasePositionRequest(args: CreateIncreasePositionRequestArgs, accounts: CreateIncreasePositionRequestAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=createIncreasePositionRequest.d.ts.map