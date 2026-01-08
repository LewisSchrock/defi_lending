import { Address, Option, Slot } from '@solana/kit';
import Decimal from 'decimal.js';
import { KaminoReserve } from './reserve';
import { Obligation } from '../@codegen/klend/accounts';
import { ElevationGroupDescription, KaminoMarket } from './market';
import { ObligationCollateral, ObligationLiquidity } from '../@codegen/klend/types';
import { ObligationType } from '../utils';
import { ActionType } from './action';
import { KaminoObligationOrder } from './obligationOrder';
export type Position = {
    reserveAddress: Address;
    mintAddress: Address;
    mintFactor: Decimal;
    /**
     * Amount of tokens in lamports, including decimal places for interest accrued (no borrow factor weighting)
     */
    amount: Decimal;
    /**
     * Market value of the position in USD (no borrow factor weighting)
     */
    marketValueRefreshed: Decimal;
};
export type PositionChange = {
    reserveAddress: Address;
    amountChangeLamports: Decimal;
};
export type ObligationStats = {
    userTotalDeposit: Decimal;
    userTotalCollateralDeposit: Decimal;
    userTotalLiquidatableDeposit: Decimal;
    userTotalBorrow: Decimal;
    userTotalBorrowBorrowFactorAdjusted: Decimal;
    borrowLimit: Decimal;
    borrowLiquidationLimit: Decimal;
    borrowUtilization: Decimal;
    netAccountValue: Decimal;
    /**
     * The obligation's current LTV, *suitable for UI display*.
     *
     * Technically, this is a ratio:
     * - of a sum of all borrows' values multiplied by reserves' borrowFactor (i.e. `userTotalBorrowBorrowFactorAdjusted`)
     * - to a sum of values of all deposits having reserve's loanToValue > 0 (i.e. `userTotalCollateralDeposit`)
     *
     * Please note that this is different from the smart contract's definition of LTV (which divides by a sum of values
     * of strictly all deposits, i.e. `userTotalDeposit`). Some parts of the SDK (e.g. obligation orders) need to use the
     * smart contract's LTV definition.
     */
    loanToValue: Decimal;
    /**
     * The LTV at which the obligation becomes subject to liquidation, *suitable for UI display*.
     *
     * Technically, this is a ratio:
     * - of a sum of values of all deposits multiplied by reserves' liquidationLtv (i.e. `borrowLiquidationLimit`)
     * - to a sum of values of all deposits having reserve's liquidationLtv > 0 (i.e. `userTotalLiquidatableDeposit`)
     *
     * Please note that this is different from the smart contract's definition of liquidation LTV (which divides by a sum
     * of values of strictly all deposits, i.e. `userTotalDeposit`). Some parts of the SDK (e.g. obligation orders) need
     * to use the smart contract's LTV definition.
     */
    liquidationLtv: Decimal;
    leverage: Decimal;
    potentialElevationGroupUpdate: number;
};
interface BorrowStats {
    borrows: Map<Address, Position>;
    userTotalBorrow: Decimal;
    userTotalBorrowBorrowFactorAdjusted: Decimal;
    positions: number;
}
interface DepositStats {
    deposits: Map<Address, Position>;
    userTotalDeposit: Decimal;
    userTotalCollateralDeposit: Decimal;
    userTotalLiquidatableDeposit: Decimal;
    borrowLimit: Decimal;
    liquidationLtv: Decimal;
    borrowLiquidationLimit: Decimal;
}
export declare class KaminoObligation {
    obligationAddress: Address;
    state: Obligation;
    /**
     * Deposits stored in a map of reserve address to position
     */
    deposits: Map<Address, Position>;
    /**
     * Borrows stored in a map of reserve address to position
     */
    borrows: Map<Address, Position>;
    refreshedStats: ObligationStats;
    obligationTag: number;
    /**
     * Initialise a new Obligation from the deserialized state
     * @param market
     * @param obligationAddress
     * @param obligation
     * @param collateralExchangeRates - rates from the market by reserve address, will be calculated if not provided
     * @param cumulativeBorrowRates - rates from the market by reserve address, will be calculated if not provided
     */
    constructor(market: KaminoMarket, obligationAddress: Address, obligation: Obligation, collateralExchangeRates: Map<Address, Decimal>, cumulativeBorrowRates: Map<Address, Decimal>);
    getObligationId(market: KaminoMarket, mintAddress1?: Option<Address>, mintAddress2?: Option<Address>): Promise<number>;
    static load(kaminoMarket: KaminoMarket, obligationAddress: Address): Promise<KaminoObligation | null>;
    static loadAll(kaminoMarket: KaminoMarket, obligationAddresses: Address[], slot?: Slot): Promise<(KaminoObligation | null)[]>;
    /**
     * @returns the obligation borrows as a list
     */
    getBorrows(): Array<Position>;
    /**
     * @returns the obligation borrows as a list
     */
    getDeposits(): Array<Position>;
    /**
     * Returns obligation orders (including the null ones, i.e. non-active positions in the orders' array).
     */
    getOrders(): Array<KaminoObligationOrder | null>;
    /**
     * Returns active obligation orders (i.e. ones that *may* have their condition met).
     */
    getActiveOrders(): Array<KaminoObligationOrder>;
    /**
     * @returns the total deposited value of the obligation (sum of all deposits)
     */
    getDepositedValue(): Decimal;
    /**
     * @returns the total borrowed value of the obligation (sum of all borrows -- no borrow factor)
     */
    getBorrowedMarketValue(): Decimal;
    /**
     * @returns the total borrowed value of the obligation (sum of all borrows -- with borrow factor weighting)
     */
    getBorrowedMarketValueBFAdjusted(): Decimal;
    /**
     * @returns total borrow power of the obligation, relative to max LTV of each asset's reserve
     */
    getMaxAllowedBorrowValue(): Decimal;
    /**
     * @returns the borrow value at which the obligation gets liquidatable
     * (relative to the liquidation threshold of each asset's reserve)
     */
    getUnhealthyBorrowValue(): Decimal;
    /**
     *
     * @returns Market value of the deposit in the specified obligation collateral/deposit asset (USD)
     */
    getDepositMarketValue(deposit: ObligationCollateral): Decimal;
    getBorrowByReserve(reserve: Address): Position | undefined;
    getDepositByReserve(reserve: Address): Position | undefined;
    getBorrowByMint(mint: Address): Position | undefined;
    getBorrowAmountByReserve(reserve: KaminoReserve): Decimal;
    getDepositByMint(mint: Address): Position | undefined;
    getDepositAmountByReserve(reserve: KaminoReserve): Decimal;
    /**
     *
     * @returns Market value of the borrow in the specified obligation liquidity/borrow asset (USD) (no borrow factor weighting)
     */
    getBorrowMarketValue(borrow: ObligationLiquidity): Decimal;
    /**
     *
     * @returns Market value of the borrow in the specified obligation liquidity/borrow asset (USD) (with borrow factor weighting)
     */
    getBorrowMarketValueBFAdjusted(borrow: ObligationLiquidity): Decimal;
    /**
     * Calculates the current ratio of borrowed value to deposited value (taking *all* deposits into account).
     *
     * Please note that the denominator here is different from the one found in `refreshedStats`:
     * - the {@link ObligationStats#loanToValue} contains a value appropriate for display on the UI (i.e. taking into
     *   account *only* the deposits having `reserve.loanToValue > 0`).
     * - the computation below follows the logic used by the KLend smart contract, and is appropriate e.g. for evaluating
     *   LTV-based obligation orders.
     */
    loanToValue(): Decimal;
    /**
     * Calculates the ratio of borrowed value to deposited value (taking *all* deposits into account) at which the
     * obligation is subject to liquidation.
     *
     * Please note that the denominator here is different from the one found in `refreshedStats`:
     * - the {@link ObligationStats#liquidationLtv} contains a value appropriate for display on the UI (i.e. taking into
     *   account *only* the deposits having `reserve.liquidationLtv > 0`).
     * - the computation below follows the logic used by the KLend smart contract, and is appropriate e.g. for evaluating
     *   LTV-based obligation orders.
     */
    liquidationLtv(): Decimal;
    /**
     * Calculate the current ratio of borrowed value to deposited value, disregarding the borrow factor.
     */
    noBfLoanToValue(): Decimal;
    /**
     * @returns the total number of positions (deposits + borrows)
     */
    getNumberOfPositions(): number;
    getNetAccountValue(): Decimal;
    getReferrer(): Option<Address>;
    /**
     * Get the loan to value and liquidation loan to value for a collateral token reserve as ratios, accounting for the obligation elevation group if it is active
     */
    getLtvForReserve(market: KaminoMarket, reserveAddress: Address): {
        maxLtv: Decimal;
        liquidationLtv: Decimal;
    };
    /**
     * @returns the potential elevation groups the obligation qualifies for
     */
    getElevationGroups(kaminoMarket: KaminoMarket): Array<number>;
    static getElevationGroupsForReserves(reserves: Array<KaminoReserve>): Array<number>;
    simulateDepositChange(obligationDeposits: ObligationCollateral[], depositChange: PositionChange, collateralExchangeRates: Map<Address, Decimal>): ObligationCollateral[];
    simulateBorrowChange(obligationBorrows: ObligationLiquidity[], borrowChange: PositionChange, cumulativeBorrowRate: Decimal): ObligationLiquidity[];
    /**
     * Calculate the newly modified stats of the obligation
     */
    getSimulatedObligationStats(params: {
        amountCollateral?: Decimal;
        amountDebt?: Decimal;
        action: ActionType;
        mintCollateral?: Address;
        mintDebt?: Address;
        market: KaminoMarket;
        reserves: Map<Address, KaminoReserve>;
        slot: Slot;
        elevationGroupOverride?: number;
    }): {
        stats: ObligationStats;
        deposits: Map<Address, Position>;
        borrows: Map<Address, Position>;
    };
    /**
     * Calculates the stats of the obligation after a hypothetical collateral swap.
     */
    getPostSwapCollObligationStats(params: {
        withdrawAmountLamports: Decimal;
        withdrawReserveAddress: Address;
        depositAmountLamports: Decimal;
        depositReserveAddress: Address;
        newElevationGroup: number;
        market: KaminoMarket;
        slot: Slot;
    }): ObligationStats;
    estimateObligationInterestRate: (market: KaminoMarket, reserve: KaminoReserve, borrow: ObligationLiquidity, currentSlot: Slot) => Decimal;
    static getOraclePx: (reserve: KaminoReserve) => Decimal;
    calculatePositions(market: KaminoMarket, obligationDeposits: ObligationCollateral[], obligationBorrows: ObligationLiquidity[], elevationGroup: number, collateralExchangeRates: Map<Address, Decimal>, cumulativeBorrowRates: Map<Address, Decimal> | null, getOraclePx?: (reserve: KaminoReserve) => Decimal): {
        borrows: Map<Address, Position>;
        deposits: Map<Address, Position>;
        refreshedStats: ObligationStats;
    };
    static calculateObligationDeposits(market: KaminoMarket, obligationDeposits: ObligationCollateral[], collateralExchangeRates: Map<Address, Decimal> | null, elevationGroup: number, getPx: (reserve: KaminoReserve) => Decimal): DepositStats;
    static calculateObligationBorrows(market: KaminoMarket, obligationBorrows: ObligationLiquidity[], cumulativeBorrowRates: Map<Address, Decimal> | null, elevationGroup: number, getPx: (reserve: KaminoReserve) => Decimal): BorrowStats;
    getMaxLoanLtvAndLiquidationLtvGivenElevationGroup(market: KaminoMarket, elevationGroup: number, slot: Slot): {
        maxLtv: Decimal;
        liquidationLtv: Decimal;
    };
    /**
     * Creates a new KaminoObligation with simulated position changes applied.
     * This allows you to model what the obligation would look like with deposits/borrows
     * without actually executing those transactions.
     *
     * @param market - The KaminoMarket instance
     * @param slot - The slot number for rate calculations
     * @param depositChanges - Optional array of deposit changes to apply
     * @param borrowChanges - Optional array of borrow changes to apply
     * @returns A new KaminoObligation instance with the changes applied
     */
    withPositionChanges(market: KaminoMarket, slot: Slot, depositChanges?: PositionChange[], borrowChanges?: PositionChange[]): KaminoObligation;
    getBorrowPower(market: KaminoMarket, liquidityMint: Address, slot: Slot, elevationGroup?: number): Decimal;
    getMaxBorrowAmountV2(market: KaminoMarket, liquidityMint: Address, slot: Slot, elevationGroup?: number): Decimal;
    getMaxBorrowAmountV2WithDeposit(market: KaminoMarket, liquidityMint: Address, slot: Slot, elevationGroup: number | undefined, depositAmountLamports: Decimal, depositReserveAddress: Address): Decimal;
    isLoanEligibleForElevationGroup(market: KaminoMarket, slot: Slot, elevationGroup: number): boolean;
    getElevationGroupsForObligation(market: KaminoMarket): ElevationGroupDescription[];
    getMaxBorrowAmount(market: KaminoMarket, liquidityMint: Address, slot: Slot, requestElevationGroup: boolean): Decimal;
    getMaxWithdrawAmount(market: KaminoMarket, tokenMint: Address, slot: Slot): Decimal;
    /**
     * Same as getMaxWithdrawAmount but assumes a repay is made first, calculating
     * the new withdraw power after the repay, without overriding the obligation itself.
     *
     * @param market - The KaminoMarket instance.
     * @param tokenMint - The liquidity mint Address.
     * @param slot - The slot number.
     * @param repayAmountLamports - The amount to repay in lamports (use U64_MAX for full repay).
     * @param repayReserveAddress - The reserve address of the borrow being repaid.
     * @returns The maximum withdraw amount as a Decimal.
     * @throws Error if the reserve is not found.
     */
    getMaxWithdrawAmountWithRepay(market: KaminoMarket, tokenMint: Address, slot: Slot, repayAmountLamports: Decimal, repayReserveAddress: Address): Decimal;
    getObligationLiquidityByReserve(reserveAddress: Address): ObligationLiquidity;
    /**
     *
     * @returns Total borrowed amount for the specified obligation liquidity/borrow asset
     */
    static getBorrowAmount(borrow: ObligationLiquidity): Decimal;
    /**
     *
     * @returns Cumulative borrow rate for the specified obligation liquidity/borrow asset
     */
    static getCumulativeBorrowRate(borrow: ObligationLiquidity): Decimal;
    static getRatesForObligation(kaminoMarket: KaminoMarket, obligation: Obligation, slot: Slot, additionalReserves?: Address[]): {
        collateralExchangeRates: Map<Address, Decimal>;
        cumulativeBorrowRates: Map<Address, Decimal>;
    };
    static addRatesForObligation(kaminoMarket: KaminoMarket, obligation: Obligation, collateralExchangeRates: Map<Address, Decimal>, cumulativeBorrowRates: Map<Address, Decimal>, slot: Slot): void;
    static getCollateralExchangeRatesForObligation(kaminoMarket: KaminoMarket, obligation: Obligation, slot: Slot, additionalReserves: Address[]): Map<Address, Decimal>;
    static addCollateralExchangeRatesForObligation(kaminoMarket: KaminoMarket, collateralExchangeRates: Map<Address, Decimal>, obligation: Obligation, slot: Slot): void;
    static getCumulativeBorrowRatesForObligation(kaminoMarket: KaminoMarket, obligation: Obligation, slot: Slot, additionalReserves?: Address[]): Map<Address, Decimal>;
    static addCumulativeBorrowRatesForObligation(kaminoMarket: KaminoMarket, cumulativeBorrowRates: Map<Address, Decimal>, obligation: Obligation, slot: Slot): void;
    /**
     * Get the borrow factor for a borrow reserve, accounting for the obligation elevation group if it is active
     * @param reserve
     * @param elevationGroup
     */
    static getBorrowFactorForReserve(reserve: KaminoReserve, elevationGroup: number): Decimal;
    /**
     * Get the loan to value and liquidation loan to value for a collateral reserve as ratios, accounting for the obligation elevation group if it is active
     * @param market
     * @param reserve
     * @param elevationGroup
     */
    static getLtvForReserve(market: KaminoMarket, reserve: KaminoReserve, elevationGroup: number): {
        maxLtv: Decimal;
        liquidationLtv: Decimal;
    };
}
export declare function isKaminoObligation(obligation: KaminoObligation | ObligationType): obligation is KaminoObligation;
export {};
//# sourceMappingURL=obligation.d.ts.map