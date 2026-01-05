"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.isBorrowingEnabled = exports.getExpectedTokenBalanceAfterBorrow = void 0;
const classes_1 = require("../classes");
const utils_1 = require("../utils");
const bn_js_1 = __importDefault(require("bn.js"));
const getExpectedTokenBalanceAfterBorrow = async (rpc, mint, owner, amountToBorrowLamports, amountToBorrowMintDecimals) => {
    const initialUserTokenABalance = await (0, utils_1.getTokenAccountBalanceDecimal)(rpc, mint, owner);
    return initialUserTokenABalance
        .add((0, classes_1.lamportsToNumberDecimal)(amountToBorrowLamports, amountToBorrowMintDecimals))
        .toDecimalPlaces(amountToBorrowMintDecimals);
};
exports.getExpectedTokenBalanceAfterBorrow = getExpectedTokenBalanceAfterBorrow;
const isBorrowingEnabled = (reserve) => {
    return reserve.state.config.borrowLimit.gt(new bn_js_1.default(0));
};
exports.isBorrowingEnabled = isBorrowingEnabled;
//# sourceMappingURL=utils.js.map