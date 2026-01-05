"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OrderActionType = exports.OrderType = void 0;
/**
 * A type of order for obligations that follow the "one optional stop-loss and one optional take-profit" convention.
 */
var OrderType;
(function (OrderType) {
    OrderType["StopLoss"] = "StopLoss";
    OrderType["TakeProfit"] = "TakeProfit";
})(OrderType || (exports.OrderType = OrderType = {}));
/**
 * A discriminator enum for {@link OrderAction};
 */
var OrderActionType;
(function (OrderActionType) {
    OrderActionType["FullRepay"] = "FullRepay";
    OrderActionType["PartialRepay"] = "PartialRepay";
})(OrderActionType || (exports.OrderActionType = OrderActionType = {}));
//# sourceMappingURL=common.js.map