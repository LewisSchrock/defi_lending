import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface IncreasePositionArgs {
    params: types.IncreasePositionParamsFields;
}
export interface IncreasePositionAccounts {
    keeper: TransactionSigner;
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
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<IncreasePositionArgs>;
export declare function increasePosition(args: IncreasePositionArgs, accounts: IncreasePositionAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=increasePosition.d.ts.map