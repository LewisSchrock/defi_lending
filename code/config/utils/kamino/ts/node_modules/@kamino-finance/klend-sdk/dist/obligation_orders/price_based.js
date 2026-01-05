"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PriceBasedOrderTriggerType = void 0;
exports.createPriceBasedOrder = createPriceBasedOrder;
exports.readPriceBasedOrder = readPriceBasedOrder;
const decimal_js_1 = __importDefault(require("decimal.js"));
const obligationOrder_1 = require("../classes/obligationOrder");
const validations_1 = require("../utils/validations");
const common_1 = require("./common");
const internal_1 = require("./internal");
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
function createPriceBasedOrder(context, orderType, specification) {
    const positionType = resolvePositionType(context); // resolving this first has an intentional side effect of validating the obligation being compatible
    const index = (0, internal_1.toOrderIndex)(orderType);
    if (specification === null) {
        return obligationOrder_1.ObligationOrderAtIndex.empty(index);
    }
    const condition = toOrderCondition(positionType, orderType, specification.trigger);
    return (0, internal_1.createConditionBasedOrder)(context, condition, specification).atIndex(index);
}
/**
 * Parses an {@link PriceBasedOrderSpecification} from the selected stop-loss or take-profit order of the given obligation.
 *
 * The given obligation is expected to be a "price-based position" - a single-debt, single-coll obligation which either
 * deposits or borrows a stablecoin (i.e. a long or short position of some token against a stablecoin).
 *
 * The selected order is expected to be of matching type (i.e. as if it was created using the
 * {@link createPriceBasedOrder()}).
 */
function readPriceBasedOrder(context, orderType) {
    const positionType = resolvePositionType(context); // resolving this first has an intentional side effect of validating the obligation being compatible
    const kaminoOrder = context.kaminoObligation.getOrders()[(0, internal_1.toOrderIndex)(orderType)];
    if (kaminoOrder === null) {
        return null;
    }
    const trigger = toTrigger(positionType, kaminoOrder.condition, orderType);
    return (0, internal_1.readTriggerBasedOrder)(kaminoOrder, trigger);
}
/**
 * A discriminator enum for {@link PriceBasedOrderTrigger};
 */
var PriceBasedOrderTriggerType;
(function (PriceBasedOrderTriggerType) {
    PriceBasedOrderTriggerType["LongStopLoss"] = "LongStopLoss";
    PriceBasedOrderTriggerType["LongTakeProfit"] = "LongTakeProfit";
    PriceBasedOrderTriggerType["ShortStopLoss"] = "ShortStopLoss";
    PriceBasedOrderTriggerType["ShortTakeProfit"] = "ShortTakeProfit";
})(PriceBasedOrderTriggerType || (exports.PriceBasedOrderTriggerType = PriceBasedOrderTriggerType = {}));
// Only internals below:
function toOrderCondition(positionType, orderType, trigger) {
    switch (positionType) {
        case PositionType.Long:
            switch (orderType) {
                case common_1.OrderType.StopLoss:
                    if (trigger.type === PriceBasedOrderTriggerType.LongStopLoss) {
                        return new obligationOrder_1.DebtCollPriceRatioAbove(invertPriceRatio(trigger.whenCollateralPriceBelow));
                    }
                    break;
                case common_1.OrderType.TakeProfit:
                    if (trigger.type === PriceBasedOrderTriggerType.LongTakeProfit) {
                        return new obligationOrder_1.DebtCollPriceRatioBelow(invertPriceRatio(trigger.whenCollateralPriceAbove));
                    }
                    break;
            }
            break;
        case PositionType.Short:
            switch (orderType) {
                case common_1.OrderType.StopLoss:
                    if (trigger.type === PriceBasedOrderTriggerType.ShortStopLoss) {
                        return new obligationOrder_1.DebtCollPriceRatioAbove(trigger.whenDebtPriceAbove);
                    }
                    break;
                case common_1.OrderType.TakeProfit:
                    if (trigger.type === PriceBasedOrderTriggerType.ShortTakeProfit) {
                        return new obligationOrder_1.DebtCollPriceRatioBelow(trigger.whenDebtPriceBelow);
                    }
                    break;
            }
            break;
    }
    throw new Error(`a ${orderType} order on a ${positionType} position cannot use ${trigger.type} condition`);
}
function toTrigger(positionType, condition, orderType) {
    switch (positionType) {
        case PositionType.Long:
            switch (orderType) {
                case common_1.OrderType.StopLoss:
                    if (condition instanceof obligationOrder_1.DebtCollPriceRatioAbove) {
                        return {
                            type: PriceBasedOrderTriggerType.LongStopLoss,
                            whenCollateralPriceBelow: invertPriceRatio(condition.minDebtCollPriceRatioExclusive),
                        };
                    }
                    break;
                case common_1.OrderType.TakeProfit:
                    if (condition instanceof obligationOrder_1.DebtCollPriceRatioBelow) {
                        return {
                            type: PriceBasedOrderTriggerType.LongTakeProfit,
                            whenCollateralPriceAbove: invertPriceRatio(condition.maxDebtCollPriceRatioExclusive),
                        };
                    }
                    break;
            }
            break;
        case PositionType.Short:
            switch (orderType) {
                case common_1.OrderType.StopLoss:
                    if (condition instanceof obligationOrder_1.DebtCollPriceRatioAbove) {
                        return {
                            type: PriceBasedOrderTriggerType.ShortStopLoss,
                            whenDebtPriceAbove: condition.minDebtCollPriceRatioExclusive,
                        };
                    }
                    break;
                case common_1.OrderType.TakeProfit:
                    if (condition instanceof obligationOrder_1.DebtCollPriceRatioBelow) {
                        return {
                            type: PriceBasedOrderTriggerType.ShortTakeProfit,
                            whenDebtPriceBelow: condition.maxDebtCollPriceRatioExclusive,
                        };
                    }
                    break;
            }
            break;
    }
    throw new Error(`a ${orderType} order on a ${positionType} position has an incompatible on-chain condition ${condition.constructor.name}`);
}
function invertPriceRatio(priceRatio) {
    return new decimal_js_1.default(1).div(priceRatio);
}
var PositionType;
(function (PositionType) {
    PositionType["Long"] = "Long";
    PositionType["Short"] = "Short";
})(PositionType || (PositionType = {}));
function resolvePositionType(context) {
    const collateralReserveAddress = (0, validations_1.getSingleElement)(context.kaminoObligation.deposits.keys(), 'deposit');
    const debtReserveAddress = (0, validations_1.getSingleElement)(context.kaminoObligation.borrows.keys(), 'borrow');
    const stablecoinReserveAddresses = collectReserveAddresses(context.kaminoMarket, context.stablecoins);
    if (stablecoinReserveAddresses.has(collateralReserveAddress)) {
        (0, validations_1.checkThat)(!stablecoinReserveAddresses.has(debtReserveAddress), 'cannot resolve long vs short position from all-stablecoins obligation');
        return PositionType.Short;
    }
    else {
        (0, validations_1.checkThat)(stablecoinReserveAddresses.has(debtReserveAddress), 'cannot resolve long vs short position from no-stablecoins obligation');
        return PositionType.Long;
    }
}
function collectReserveAddresses(kaminoMarket, symbolOrMintAddresses) {
    return new Set(symbolOrMintAddresses.map((symbolOrMintAddress) => typeof symbolOrMintAddress === 'string'
        ? kaminoMarket.getExistingReserveBySymbol(symbolOrMintAddress).address
        : kaminoMarket.getExistingReserveByMint(symbolOrMintAddress).address));
}
//# sourceMappingURL=price_based.js.map