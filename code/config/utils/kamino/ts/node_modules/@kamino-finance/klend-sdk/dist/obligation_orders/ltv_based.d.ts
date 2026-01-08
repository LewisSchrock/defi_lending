import { ObligationOrderAtIndex } from '../classes/obligationOrder';
import { OrderContext, OrderSpecification, OrderType } from './common';
/**
 * Creates an LTV-based {@link ObligationOrderAtIndex} based on the given stop-loss or take-profit specification.
 *
 * The returned object can then be passed directly to {@link KaminoAction.buildSetObligationOrderIxn()} to build an
 * instruction which replaces (or cancels, if the specification is `null`) the given obligation's stop-loss or
 * take-profit order on-chain.
 *
 * The given obligation cannot use 0-LTV collaterals (see {@link checkObligationCompatible()} for rationale).
 */
export declare function createLtvBasedOrder(context: OrderContext, orderType: OrderType, specification: LtvBasedOrderSpecification | null): ObligationOrderAtIndex;
/**
 * Parses an {@link OrderSpecification} from the selected stop-loss or take-profit order of the given obligation.
 *
 * The given obligation cannot use 0-LTV collaterals (see {@link checkObligationCompatible()} for rationale).
 *
 * The selected order is expected to be of matching type (i.e. as if it was created using the
 * {@link createLtvBasedOrder()}).
 */
export declare function readLtvBasedOrder(context: OrderContext, orderType: OrderType): LtvBasedOrderSpecification | null;
/**
 * A high-level specification of an LTV-based order.
 */
export type LtvBasedOrderSpecification = OrderSpecification<LtvBasedOrderTrigger>;
/**
 * A discriminator enum for {@link LtvBasedOrderTrigger};
 */
export declare enum LtvBasedOrderTriggerType {
    StopLoss = "StopLoss",
    TakeProfit = "TakeProfit"
}
/**
 * One of possible triggers depending on the obligation's type and the price bracket's side.
 */
export type LtvBasedOrderTrigger = StopLoss | TakeProfit;
/**
 * A trigger for a stop-loss on LTV.
 */
export type StopLoss = {
    type: LtvBasedOrderTriggerType.StopLoss;
    whenLtvPctAbove: number;
};
/**
 * A trigger for a take-profit on LTV.
 */
export type TakeProfit = {
    type: LtvBasedOrderTriggerType.TakeProfit;
    whenLtvPctBelow: number;
};
//# sourceMappingURL=ltv_based.d.ts.map