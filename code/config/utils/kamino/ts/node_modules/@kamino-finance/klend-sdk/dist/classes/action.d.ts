import { Address, AccountMeta, Instruction, Option, Slot, TransactionSigner } from '@solana/kit';
import BN from 'bn.js';
import { ObligationType, ScopePriceRefreshConfig } from '../utils';
import { KaminoMarket } from './market';
import { KaminoObligation } from './obligation';
import { KaminoReserve } from './reserve';
import { Scope } from '@kamino-finance/scope-sdk';
import { ObligationOrderAtIndex } from './obligationOrder';
export type ActionType = 'deposit' | 'borrow' | 'withdraw' | 'repay' | 'mint' | 'redeem' | 'depositCollateral' | 'liquidate' | 'depositAndBorrow' | 'repayAndWithdraw' | 'refreshObligation' | 'requestElevationGroup' | 'withdrawReferrerFees' | 'repayAndWithdrawV2' | 'depositAndWithdraw';
export type AuxiliaryIx = 'setup' | 'inBetween' | 'cleanup';
export declare class KaminoAction {
    kaminoMarket: KaminoMarket;
    reserve: KaminoReserve;
    outflowReserve: KaminoReserve | undefined;
    owner: TransactionSigner;
    payer: TransactionSigner;
    obligation: KaminoObligation | ObligationType;
    referrer: Option<Address>;
    /**
     * Null unless the obligation is not passed
     */
    obligationType: ObligationType | null;
    mint: Address;
    secondaryMint?: Address;
    positions?: number;
    amount: BN;
    outflowAmount?: BN;
    computeBudgetIxs: Array<Instruction>;
    computeBudgetIxsLabels: Array<string>;
    setupIxs: Array<Instruction>;
    setupIxsLabels: Array<string>;
    inBetweenIxs: Array<Instruction>;
    inBetweenIxsLabels: Array<string>;
    lendingIxs: Array<Instruction>;
    lendingIxsLabels: Array<string>;
    cleanupIxs: Array<Instruction>;
    cleanupIxsLabels: Array<string>;
    refreshFarmsCleanupTxnIxs: Array<Instruction>;
    refreshFarmsCleanupTxnIxsLabels: Array<string>;
    depositReserves: Array<Address>;
    borrowReserves: Array<Address>;
    preLoadedDepositReservesSameTx: Array<Address>;
    currentSlot: Slot;
    private constructor();
    static initialize(action: ActionType, amount: string | BN, mint: Address, owner: TransactionSigner, kaminoMarket: KaminoMarket, obligation: KaminoObligation | ObligationType, referrer?: Option<Address>, currentSlot?: Slot, payer?: TransactionSigner): Promise<KaminoAction>;
    private static getUserAccountAddresses;
    private static loadObligation;
    static buildRefreshObligationTxns(kaminoMarket: KaminoMarket, payer: TransactionSigner, obligation: KaminoObligation, extraComputeBudget?: number, // if > 0 then adds the ix
    currentSlot?: Slot): Promise<KaminoAction>;
    static buildRequestElevationGroupTxns(kaminoMarket: KaminoMarket, owner: TransactionSigner, obligation: KaminoObligation, elevationGroup: number, extraComputeBudget?: number, // if > 0 then adds the ix
    currentSlot?: Slot): Promise<KaminoAction>;
    static buildDepositTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, // to be requested *before* the deposit
    initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, currentSlot?: Slot, overrideElevationGroupRequest?: number | undefined): Promise<KaminoAction>;
    addScopeRefreshIxs(scope: Scope, tokens: number[], scopeConfig: Address): Promise<void>;
    static buildBorrowTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, currentSlot?: Slot, overrideElevationGroupRequest?: number | undefined): Promise<KaminoAction>;
    static buildDepositReserveLiquidityTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas
    requestElevationGroup?: boolean, referrer?: Option<Address>, currentSlot?: Slot): Promise<KaminoAction>;
    static buildRedeemReserveCollateralTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas
    requestElevationGroup?: boolean, referrer?: Option<Address>, currentSlot?: Slot): Promise<KaminoAction>;
    static buildDepositObligationCollateralTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, currentSlot?: Slot): Promise<KaminoAction>;
    static buildDepositAndBorrowTxns(kaminoMarket: KaminoMarket, depositAmount: string | BN, depositMint: Address, borrowAmount: string | BN, borrowMint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, currentSlot?: Slot): Promise<KaminoAction>;
    static buildDepositAndWithdrawV2Txns(kaminoMarket: KaminoMarket, depositAmount: string | BN, depositMint: Address, withdrawAmount: string | BN, withdrawMint: Address, owner: TransactionSigner, currentSlot: Slot, obligation: KaminoObligation | ObligationType, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>): Promise<KaminoAction>;
    static buildRepayAndWithdrawV2Txns(kaminoMarket: KaminoMarket, repayAmount: string | BN, repayMint: Address, withdrawAmount: string | BN, withdrawMint: Address, payer: TransactionSigner, currentSlot: Slot, obligation: KaminoObligation | ObligationType, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>): Promise<KaminoAction>;
    static buildRepayAndWithdrawTxns(kaminoMarket: KaminoMarket, repayAmount: string | BN, repayMint: Address, withdrawAmount: string | BN, withdrawMint: Address, payer: TransactionSigner, currentSlot: Slot, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>): Promise<KaminoAction>;
    static buildWithdrawTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas,
    requestElevationGroup?: boolean, // to be requested *after* the withdraw
    initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, currentSlot?: Slot, overrideElevationGroupRequest?: number, obligationCustomizations?: {
        addedDepositReserves?: Address[];
    }): Promise<KaminoAction>;
    /**
     *
     * @param kaminoMarket
     * @param amount
     * @param mint
     * @param owner
     * @param obligation - obligation to repay or the PDA seeds
     * @param useV2Ixs
     * @param scopeRefreshConfig
     * @param currentSlot
     * @param payer - if not set then owner is used
     * @param extraComputeBudget - if > 0 then adds the ix
     * @param includeAtaIxs - if true it includes create and close wsol and token atas
     * @param requestElevationGroup
     * @param initUserMetadata
     * @param referrer
     */
    static buildRepayTxns(kaminoMarket: KaminoMarket, amount: string | BN, mint: Address, owner: TransactionSigner, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, currentSlot: Slot, payer?: TransactionSigner, extraComputeBudget?: number, includeAtaIxs?: boolean, requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>): Promise<KaminoAction>;
    static buildLiquidateTxns(kaminoMarket: KaminoMarket, amount: string | BN, minCollateralReceiveAmount: string | BN, repayTokenMint: Address, withdrawTokenMint: Address, liquidator: TransactionSigner, obligationOwner: Address, obligation: KaminoObligation | ObligationType, useV2Ixs: boolean, scopeRefreshConfig?: ScopePriceRefreshConfig | undefined, extraComputeBudget?: number, // if > 0 then adds the ix
    includeAtaIxs?: boolean, // if true it includes create and close wsol and token atas, and creates all other token atas if they don't exist
    requestElevationGroup?: boolean, initUserMetadata?: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, referrer?: Option<Address>, maxAllowedLtvOverridePercent?: number, currentSlot?: Slot): Promise<KaminoAction>;
    static buildWithdrawReferrerFeeTxns(owner: TransactionSigner, tokenMint: Address, kaminoMarket: KaminoMarket, currentSlot?: Slot): Promise<KaminoAction>;
    /**
     * Builds an instruction for setting the new state of one of the given obligation's orders.
     *
     * In other words: it will overwrite the given slot in the {@link Obligation.orders} array. This possibly includes
     * setting the `null` state (i.e. cancelling the order).
     */
    static buildSetObligationOrderIxn(owner: TransactionSigner, kaminoMarket: KaminoMarket, obligation: KaminoObligation, orderAtIndex: ObligationOrderAtIndex): Instruction;
    addDepositReserveLiquidityIx(): Promise<void>;
    addRedeemReserveCollateralIx(): Promise<void>;
    addDepositIx(): Promise<void>;
    addDepositIxV2(): Promise<void>;
    addDepositObligationCollateralIx(): Promise<void>;
    addDepositObligationCollateralIxV2(): Promise<void>;
    addBorrowIx(): Promise<void>;
    addBorrowIxV2(): Promise<void>;
    addWithdrawIx(collateralAmount: BN): Promise<void>;
    addWithdrawIxV2(collateralAmount: BN): Promise<void>;
    addRepayIx(): Promise<void>;
    addRepayIxV2(): Promise<void>;
    addRepayAndWithdrawV2Ixs(withdrawCollateralAmount: BN): Promise<void>;
    addDepositAndWithdrawV2Ixs(withdrawCollateralAmount: BN): Promise<void>;
    addDepositAndBorrowIx(): Promise<void>;
    addDepositAndBorrowIxV2(): Promise<void>;
    addRepayAndWithdrawIxs(withdrawCollateralAmount: BN): Promise<void>;
    addRepayAndWithdrawIxsV2(withdrawCollateralAmount: BN): Promise<void>;
    addLiquidateIx(maxAllowedLtvOverridePercent?: number): Promise<void>;
    addLiquidateIxV2(maxAllowedLtvOverridePercent?: number): Promise<void>;
    addInBetweenIxs(action: ActionType, includeAtaIxs: boolean, requestElevationGroup: boolean, addInitObligationForFarm: boolean, useV2Ixs: boolean): Promise<void>;
    addRefreshObligation(crank: TransactionSigner): Promise<void>;
    addSupportIxsWithoutInitObligation(action: ActionType, includeAtaIxs: boolean, useV2Ixs: boolean, addAsSupportIx?: AuxiliaryIx, requestElevationGroup?: boolean, addInitObligationForFarm?: boolean, twoTokenAction?: boolean, overrideElevationGroupRequest?: number): Promise<void>;
    addSupportIxs(action: ActionType, includeAtaIxs: boolean, requestElevationGroup: boolean, addInitObligationForFarm: boolean, useV2Ixs: boolean, scopeRefreshConfig: ScopePriceRefreshConfig | undefined, initUserMetadata: {
        skipInitialization: boolean;
        skipLutCreation: boolean;
    }, twoTokenAction?: boolean, overrideElevationGroupRequest?: number): Promise<void>;
    private static optionalAccount;
    private addRefreshReserveIxs;
    static getRefreshAllReserves(kaminoMarket: KaminoMarket, reserves: Address[]): Instruction[];
    private addRefreshObligationIx;
    private addRequestElevationIx;
    private addRefreshFarmsForReserve;
    private addRefreshFarmsCleanupTxnIxsToCleanupIxs;
    private addInitObligationForFarm;
    private addInitObligationIxs;
    private addInitUserMetadataIxs;
    private addInitReferrerTokenStateIx;
    private addWithdrawReferrerFeesIxs;
    private addComputeBudgetIx;
    private addAtaIxs;
    private updateWSOLAccount;
    static initializeMultiTokenAction(kaminoMarket: KaminoMarket, action: ActionType, inflowAmount: string | BN, inflowTokenMint: Address, outflowTokenMint: Address, signer: TransactionSigner, obligationOwner: Address, obligation: KaminoObligation | ObligationType, outflowAmount?: string | BN, referrer?: Option<Address>, currentSlot?: Slot): Promise<KaminoAction>;
    static initializeWithdrawReferrerFees(mint: Address, owner: TransactionSigner, kaminoMarket: KaminoMarket, currentSlot?: Slot): Promise<{
        axn: KaminoAction;
        createAtaIxs: Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>[];
    }>;
    getWithdrawCollateralAmount(reserve: KaminoReserve, amount: BN): BN;
    getObligationPda(): Promise<Address>;
    isObligationInitialized(): boolean;
    getAdditionalDepositReservesList(): Address[];
    private static getReferrerMetadataAccount;
    private getReferrerTokenStateAccountMeta;
    private getReferrerTokenStateAddress;
    getUserTokenAccountAddress(reserve: KaminoReserve): Promise<Address>;
    getTokenAccountAddressByUser(reserve: KaminoReserve, user: Address): Promise<Address>;
    getUserCollateralAccountAddress(reserve: KaminoReserve): Promise<Address>;
    static actionToIxs(action: KaminoAction): Array<Instruction>;
    static actionToLendingIxs(action: KaminoAction): Array<Instruction>;
    static actionToIxLabels(action: KaminoAction): Array<string>;
    static actionToLendingIxLabels(action: KaminoAction): Array<string>;
    private static getFarmAccountsForReserve;
    private static getReferrerKey;
    private static getReferrerTokenStateAddressImpl;
}
//# sourceMappingURL=action.d.ts.map