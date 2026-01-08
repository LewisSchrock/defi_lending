"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.toOrderIndex = toOrderIndex;
exports.createConditionBasedOrder = createConditionBasedOrder;
exports.readTriggerBasedOrder = readTriggerBasedOrder;
const decimal_js_1 = __importDefault(require("decimal.js"));
const obligationOrder_1 = require("../classes/obligationOrder");
const validations_1 = require("../utils/validations");
const utils_1 = require("../utils");
const common_1 = require("./common");
// These methods are exported, buy only used internally within the obligation orders utils:
function toOrderIndex(orderType) {
    switch (orderType) {
        case common_1.OrderType.StopLoss:
            return 0;
        case common_1.OrderType.TakeProfit:
            return 1;
    }
}
function createConditionBasedOrder(context, condition, specification) {
    (0, validations_1.checkThat)(condition.evaluate(context.kaminoObligation) === null, `cannot create an immediately-triggered order`);
    const opportunity = toOrderOpportunity(context, specification.action);
    const [minExecutionBonusRate, maxExecutionBonusRate] = toExecutionBonusRates(specification.executionBonusBpsRange);
    return new obligationOrder_1.KaminoObligationOrder(condition, opportunity, minExecutionBonusRate, maxExecutionBonusRate);
}
function readTriggerBasedOrder(kaminoOrder, trigger) {
    return {
        trigger,
        action: toAction(kaminoOrder.opportunity),
        executionBonusBpsRange: toExecutionBonusBps(kaminoOrder.minExecutionBonusRate, kaminoOrder.maxExecutionBonusRate),
    };
}
// Only internals below:
function toOrderOpportunity(context, action) {
    switch (action.type) {
        case common_1.OrderActionType.FullRepay:
            return new obligationOrder_1.DeleverageAllDebt();
        case common_1.OrderActionType.PartialRepay:
            const { repayDebtAmountLamports } = action;
            (0, validations_1.checkThat)(repayDebtAmountLamports.gt(0), `repay amount must be positive; got ${repayDebtAmountLamports}`);
            const availableDebtAmountLamports = (0, validations_1.getSingleElement)(context.kaminoObligation.getBorrows(), 'borrow').amount;
            (0, validations_1.checkThat)(repayDebtAmountLamports.lte(availableDebtAmountLamports), `partial repay amount ${repayDebtAmountLamports} cannot exceed the borrowed amount ${availableDebtAmountLamports}`);
            return new obligationOrder_1.DeleverageDebtAmount(action.repayDebtAmountLamports);
    }
}
function toExecutionBonusRates(executionBonusBpsRange) {
    const [minExecutionBonusRate, maxExecutionBonusRate] = executionBonusBpsRange.map((bps) => new decimal_js_1.default(bps).div(utils_1.ONE_HUNDRED_PCT_IN_BPS));
    (0, validations_1.checkThat)(minExecutionBonusRate.gte(0), `execution bonus rate cannot be negative: ${minExecutionBonusRate}`);
    (0, validations_1.checkThat)(maxExecutionBonusRate.gte(minExecutionBonusRate), `max execution bonus rate ${maxExecutionBonusRate} cannot be lower than min ${minExecutionBonusRate}`);
    return [minExecutionBonusRate, maxExecutionBonusRate];
}
function toAction(opportunity) {
    if (opportunity instanceof obligationOrder_1.DeleverageAllDebt) {
        return {
            type: common_1.OrderActionType.FullRepay,
        };
    }
    if (opportunity instanceof obligationOrder_1.DeleverageDebtAmount) {
        return {
            type: common_1.OrderActionType.PartialRepay,
            repayDebtAmountLamports: opportunity.amount,
        };
    }
    throw new Error(`incompatible on-chain opportunity ${opportunity.constructor.name}`);
}
function toExecutionBonusBps(minExecutionBonusRate, maxExecutionBonusRate) {
    return [minExecutionBonusRate, maxExecutionBonusRate].map((rate) => new decimal_js_1.default(rate).mul(utils_1.ONE_HUNDRED_PCT_IN_BPS).toNumber());
}
//# sourceMappingURL=internal.js.map