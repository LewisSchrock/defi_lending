import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RepayObligationLiquidityV2Args {
    liquidityAmount: BN;
}
export interface RepayObligationLiquidityV2Accounts {
    repayAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        repayReserve: Address;
        reserveLiquidityMint: Address;
        reserveDestinationLiquidity: Address;
        userSourceLiquidity: Address;
        tokenProgram: Address;
        instructionSysvarAccount: Address;
    };
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    lendingMarketAuthority: Address;
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<RepayObligationLiquidityV2Args>;
export declare function repayObligationLiquidityV2(args: RepayObligationLiquidityV2Args, accounts: RepayObligationLiquidityV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=repayObligationLiquidityV2.d.ts.map