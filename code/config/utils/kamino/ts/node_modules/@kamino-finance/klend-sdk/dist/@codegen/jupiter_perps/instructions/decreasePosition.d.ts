import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DecreasePositionArgs {
    params: types.DecreasePositionParamsFields;
}
export interface DecreasePositionAccounts {
    keeper: TransactionSigner;
    keeperAta: Option<Address>;
    owner: Address;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    positionRequest: Address;
    positionRequestAta: Address;
    position: Address;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
    collateralCustodyOracleAccount: Address;
    collateralCustodyTokenAccount: Address;
    instruction: Address;
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<DecreasePositionArgs>;
export declare function decreasePosition(args: DecreasePositionArgs, accounts: DecreasePositionAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=decreasePosition.d.ts.map