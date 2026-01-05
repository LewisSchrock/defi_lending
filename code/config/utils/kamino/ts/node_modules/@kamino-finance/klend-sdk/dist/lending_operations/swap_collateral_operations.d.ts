import { KaminoMarket, KaminoObligation } from '../classes';
import { SwapIxsProvider, SwapQuoteProvider } from '../leverage';
import { Account, Address, Instruction, Option, Slot, TransactionSigner } from '@solana/kit';
import Decimal from 'decimal.js';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
/**
 * Inputs to the `getSwapCollIxs()` operation.
 */
export interface SwapCollIxsInputs<QuoteResponse> {
    /**
     * The amount of source collateral to be swapped-in for the target collateral.
     * This value will be treated exactly (i.e. slippage is not applied here) and thus must not exceed the collateral's
     * total amount.
     */
    sourceCollSwapAmount: Decimal;
    /**
     * If true, the source collateral will be closed - whatever amount is left after withdrawing `sourceCollSwapAmount`
     * will be transferred to the user.
     */
    isClosingSourceColl: boolean;
    /**
     * The mint of the source collateral token (i.e. the current one).
     */
    sourceCollTokenMint: Address;
    /**
     * The mint of the target collateral token (i.e. the new one).
     */
    targetCollTokenMint: Address;
    /**
     * An elevation group ID that the obligation should end up with after the collateral swap - it will be requested by
     * this operation (if different from the obligation's current elevation group).
     */
    newElevationGroup: number;
    market: KaminoMarket;
    owner: TransactionSigner;
    obligation: KaminoObligation;
    referrer: Option<Address>;
    currentSlot: Slot;
    budgetAndPriorityFeeIxs?: Instruction[];
    scopeRefreshIx: Instruction[];
    useV2Ixs: boolean;
    quoter: SwapQuoteProvider<QuoteResponse>;
    swapper: SwapIxsProvider<QuoteResponse>;
    logger?: (msg: string, ...extra: any[]) => void;
}
/**
 * Outputs from the `getSwapCollIxs()` operation.
 */
export interface SwapCollIxsOutputs<QuoteResponse> {
    /**
     * Instructions for on-chain execution.
     */
    ixs: Instruction[];
    /**
     * Required LUTs.
     */
    lookupTables: Account<AddressLookupTable>[];
    /**
     * Whether the swap is using V2 instructions.
     */
    useV2Ixs: boolean;
    /**
     * Informational-only details of the token amounts/fees/rates that were used during construction of `ixs`.
     */
    simulationDetails: {
        /**
         * Details related to the flash-loan operation needed during collateral swap.
         */
        flashLoan: {
            /**
             * The amount of flash-borrowed target collateral.
             * It is also *exactly the amount of target collateral that gets added to the obligation*.
             */
            targetCollFlashBorrowedAmount: Decimal;
            /**
             * The flash-repaid amount.
             * Simply a `targetCollFlashBorrowedAmount` + any flash-loan fees.
             */
            targetCollFlashRepaidAmount: Decimal;
        };
        /**
         * Details related to the external DEX's swap operation (i.e. `swapper` input) needed during collateral swap.
         */
        externalSwap: {
            /**
             * The amount swapped-in to an external DEX.
             * It is also *exactly the amount of source collateral that gets removed from the obligation* (i.e. echoed back
             * `sourceCollSwapAmount` input).
             */
            sourceCollSwapInAmount: Decimal;
            /**
             * The amount swapped-out from an external DEX.
             * Please note that this field will be equal to the `flashBorrow.targetCollFlashRepaidAmount`, but an actual
             * on-chain swap-out is subject to slippage.
             */
            targetCollSwapOutAmount: Decimal;
            /**
             * The verbatim response coming from the input `quoter`.
             */
            quoteResponse?: QuoteResponse;
        };
    };
}
/**
 * Constructs instructions needed to partially/fully swap the given source collateral for some other collateral type.
 */
export declare function getSwapCollIxs<QuoteResponse>(inputs: SwapCollIxsInputs<QuoteResponse>): Promise<Array<SwapCollIxsOutputs<QuoteResponse>>>;
//# sourceMappingURL=swap_collateral_operations.d.ts.map