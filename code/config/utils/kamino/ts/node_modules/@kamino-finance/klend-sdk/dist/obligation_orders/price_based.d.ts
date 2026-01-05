import Decimal from 'decimal.js';
import { ObligationOrderAtIndex } from '../classes/obligationOrder';
import { Address } from '@solana/kit';
import { OrderContext, OrderSpecification, OrderType } from './common';
/**
 * Creates a price-based {@link ObligationOrderAtIndex} based on the given stop-loss or take-profit specification.
 *
 * The returned object can then be passed directly to {@link KaminoAction.buildSetObligationOrderIxn()} to build an
 * instruction which replaces (or cancels, if the specification is `null`) the given obligation's stop-loss or
 * take-profit order on-chain.
 *
 * The given obligation is expected to be a "price-based position" - a single-debt, single-coll obligation which either
 * deposits or borrows a stablecoin (i.e. a long or short position of some token against a stablecoin).
 */
export declare function createPriceBasedOrder(context: PriceBasedOrderContext, orderType: OrderType, specification: PriceBasedOrderSpecification | null): ObligationOrderAtIndex;
/**
 * Parses an {@link PriceBasedOrderSpecification} from the selected stop-loss or take-profit order of the given obligation.
 *
 * The given obligation is expected to be a "price-based position" - a single-debt, single-coll obligation which either
 * deposits or borrows a stablecoin (i.e. a long or short position of some token against a stablecoin).
 *
 * The selected order is expected to be of matching type (i.e. as if it was created using the
 * {@link createPriceBasedOrder()}).
 */
export declare function readPriceBasedOrder(context: PriceBasedOrderContext, orderType: OrderType): PriceBasedOrderSpecification | null;
/**
 * An extended {@link OrderContext} needed to interpret orders on "price-based position" obligations.
 */
export type PriceBasedOrderContext = OrderContext & {
    stablecoins: SymbolOrMintAddress[];
};
/**
 * A convenient multi-way of specifying a token.
 */
export type SymbolOrMintAddress = string | Address;
/**
 * A high-level specification of a price-based order.
 */
export type PriceBasedOrderSpecification = OrderSpecification<PriceBasedOrderTrigger>;
/**
 * A discriminator enum for {@link PriceBasedOrderTrigger};
 */
export declare enum PriceBasedOrderTriggerType {
    LongStopLoss = "LongStopLoss",
    LongTakeProfit = "LongTakeProfit",
    ShortStopLoss = "ShortStopLoss",
    ShortTakeProfit = "ShortTakeProfit"
}
/**
 * One of possible triggers depending on the obligation's type and the price bracket's side.
 */
export type PriceBasedOrderTrigger = LongStopLoss | LongTakeProfit | ShortStopLoss | ShortTakeProfit;
/**
 * A trigger for a stop-loss on a long position.
 */
export type LongStopLoss = {
    type: PriceBasedOrderTriggerType.LongStopLoss;
    whenCollateralPriceBelow: Decimal;
};
/**
 * A trigger for a take-profit on a long position.
 */
export type LongTakeProfit = {
    type: PriceBasedOrderTriggerType.LongTakeProfit;
    whenCollateralPriceAbove: Decimal;
};
/**
 * A trigger for a stop-loss on a short position.
 */
export type ShortStopLoss = {
    type: PriceBasedOrderTriggerType.ShortStopLoss;
    whenDebtPriceAbove: Decimal;
};
/**
 * A trigger for a take-profit on a short position.
 */
export type ShortTakeProfit = {
    type: PriceBasedOrderTriggerType.ShortTakeProfit;
    whenDebtPriceBelow: Decimal;
};
//# sourceMappingURL=price_based.d.ts.map