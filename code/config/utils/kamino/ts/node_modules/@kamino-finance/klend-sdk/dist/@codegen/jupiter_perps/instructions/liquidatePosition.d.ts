import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface LiquidatePositionArgs {
    params: types.LiquidatePositionParamsFields;
}
export interface LiquidatePositionAccounts {
    signer: TransactionSigner;
    receivingAccount: Address;
    rewardReceivingAccount: Address;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
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
export declare const layout: import("buffer-layout").Layout<LiquidatePositionArgs>;
export declare function liquidatePosition(args: LiquidatePositionArgs, accounts: LiquidatePositionAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=liquidatePosition.d.ts.map