import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface BorrowObligationLiquidityV2Args {
    liquidityAmount: BN;
}
export interface BorrowObligationLiquidityV2Accounts {
    borrowAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        lendingMarketAuthority: Address;
        borrowReserve: Address;
        borrowReserveLiquidityMint: Address;
        reserveSourceLiquidity: Address;
        borrowReserveLiquidityFeeReceiver: Address;
        userDestinationLiquidity: Address;
        referrerTokenState: Option<Address>;
        tokenProgram: Address;
        instructionSysvarAccount: Address;
    };
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<BorrowObligationLiquidityV2Args>;
export declare function borrowObligationLiquidityV2(args: BorrowObligationLiquidityV2Args, accounts: BorrowObligationLiquidityV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=borrowObligationLiquidityV2.d.ts.map