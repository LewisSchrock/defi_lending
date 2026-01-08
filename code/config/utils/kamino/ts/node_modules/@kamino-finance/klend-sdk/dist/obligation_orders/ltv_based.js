"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LtvBasedOrderTriggerType = void 0;
exports.createLtvBasedOrder = createLtvBasedOrder;
exports.readLtvBasedOrder = readLtvBasedOrder;
const decimal_js_1 = __importDefault(require("decimal.js"));
const obligationOrder_1 = require("../classes/obligationOrder");
const validations_1 = require("../utils/validations");
const common_1 = require("./common");
const internal_1 = require("./internal");
/**
 * Creates an LTV-based {@link ObligationOrderAtIndex} based on the given stop-loss or take-profit specification.
 *
 * The returned object can then be passed directly to {@link KaminoAction.buildSetObligationOrderIxn()} to build an
 * instruction which replaces (or cancels, if the specification is `null`) the given obligation's stop-loss or
 * take-profit order on-chain.
 *
 * The given obligation cannot use 0-LTV collaterals (see {@link checkObligationCompatible()} for rationale).
 */
function createLtvBasedOrder(context, orderType, specification) {
    checkObligationCompatible(context);
    const index = (0, internal_1.toOrderIndex)(orderType);
    if (specification === null) {
        return obligationOrder_1.ObligationOrderAtIndex.empty(index);
    }
    const condition = toOrderCondition(orderType, specification.trigger);
    (0, validations_1.checkThat)(condition.threshold().gte(MIN_LTV_THRESHOLD) && condition.threshold().lte(MAX_LTV_THRESHOLD), `LTV-based trigger outside valid range [${MIN_LTV_THRESHOLD}%; ${MAX_LTV_THRESHOLD}%]: ${condition.threshold()}%`);
    return (0, internal_1.createConditionBasedOrder)(context, condition, specification).atIndex(index);
}
/**
 * Parses an {@link OrderSpecification} from the selected stop-loss or take-profit order of the given obligation.
 *
 * The given obligation cannot use 0-LTV collaterals (see {@link checkObligationCompatible()} for rationale).
 *
 * The selected order is expected to be of matching type (i.e. as if it was created using the
 * {@link createLtvBasedOrder()}).
 */
function readLtvBasedOrder(context, orderType) {
    checkObligationCompatible(context);
    const kaminoOrder = context.kaminoObligation.getOrders()[(0, internal_1.toOrderIndex)(orderType)];
    if (kaminoOrder === null) {
        return null;
    }
    const trigger = toTrigger(kaminoOrder.condition, orderType);
    return (0, internal_1.readTriggerBasedOrder)(kaminoOrder, trigger);
}
/**
 * A discriminator enum for {@link LtvBasedOrderTrigger};
 */
var LtvBasedOrderTriggerType;
(function (LtvBasedOrderTriggerType) {
    LtvBasedOrderTriggerType["StopLoss"] = "StopLoss";
    LtvBasedOrderTriggerType["TakeProfit"] = "TakeProfit";
})(LtvBasedOrderTriggerType || (exports.LtvBasedOrderTriggerType = LtvBasedOrderTriggerType = {}));
// Only internals below:
const FULL_PCT = 100;
const MIN_LTV_THRESHOLD = 0.01;
const MAX_LTV_THRESHOLD = 0.99;
function checkObligationCompatible({ kaminoMarket, kaminoObligation }) {
    for (const depositReserveAddress of kaminoObligation.deposits.keys()) {
        const depositReserve = kaminoMarket.getExistingReserveByAddress(depositReserveAddress);
        // Note: the seemingly over-cautious requirement below ensures that the user-facing LTV calculation gives the same
        // result as on the Klend SC side (they differ in the handling of 0-LTV collaterals; see
        // `KaminoObligation.loanToValue()` doc for details). We may unify the 0-LTV handling some day and remove this.
        (0, validations_1.checkThat)(depositReserve.state.config.loanToValuePct !== 0, `LTV-based orders cannot be used with a 0-LTV collateral: ${depositReserve.symbol}`);
    }
}
function toOrderCondition(orderType, trigger) {
    switch (orderType) {
        case common_1.OrderType.StopLoss:
            if (trigger.type === LtvBasedOrderTriggerType.StopLoss) {
                return new obligationOrder_1.UserLtvAbove(new decimal_js_1.default(trigger.whenLtvPctAbove).div(FULL_PCT));
            }
            break;
        case common_1.OrderType.TakeProfit:
            if (trigger.type === LtvBasedOrderTriggerType.TakeProfit) {
                return new obligationOrder_1.UserLtvBelow(new decimal_js_1.default(trigger.whenLtvPctBelow).div(FULL_PCT));
            }
            break;
    }
    throw new Error(`an LTV-based ${orderType} order cannot use ${trigger.type} condition`);
}
function toTrigger(condition, orderType) {
    switch (orderType) {
        case common_1.OrderType.StopLoss:
            if (condition instanceof obligationOrder_1.UserLtvAbove) {
                return {
                    type: LtvBasedOrderTriggerType.StopLoss,
                    whenLtvPctAbove: condition.minUserLtvExclusive.mul(FULL_PCT).toNumber(),
                };
            }
            break;
        case common_1.OrderType.TakeProfit:
            if (condition instanceof obligationOrder_1.UserLtvBelow) {
                return {
                    type: LtvBasedOrderTriggerType.TakeProfit,
                    whenLtvPctBelow: condition.maxUserLtvExclusive.mul(FULL_PCT).toNumber(),
                };
            }
            break;
    }
    throw new Error(`an LTV-based ${orderType} order has an incompatible on-chain condition ${condition.constructor.name}`);
}
//# sourceMappingURL=ltv_based.js.map