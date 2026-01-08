import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RepayObligationLiquidityArgs {
    liquidityAmount: BN;
}
export interface RepayObligationLiquidityAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    repayReserve: Address;
    reserveLiquidityMint: Address;
    reserveDestinationLiquidity: Address;
    userSourceLiquidity: Address;
    tokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<RepayObligationLiquidityArgs>;
export declare function repayObligationLiquidity(args: RepayObligationLiquidityArgs, accounts: RepayObligationLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=repayObligationLiquidity.d.ts.map