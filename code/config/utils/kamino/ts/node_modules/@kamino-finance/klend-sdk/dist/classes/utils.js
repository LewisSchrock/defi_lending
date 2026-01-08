"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.positiveOrZero = exports.isEmptyObject = exports.valueOrZero = exports.isSolMint = exports.parseTokenSymbol = exports.getBorrowRate = exports.interpolate = exports.estimateCurrentScore = exports.calculateNewScore = void 0;
exports.parseZeroPaddedUtf8 = parseZeroPaddedUtf8;
exports.renderZeroPaddedUtf8 = renderZeroPaddedUtf8;
exports.sleep = sleep;
exports.numberToLamportsDecimal = numberToLamportsDecimal;
exports.lamportsToNumberDecimal = lamportsToNumberDecimal;
exports.lamportsToDecimal = lamportsToDecimal;
exports.calculateAPYFromAPR = calculateAPYFromAPR;
exports.calculateAPRFromAPY = calculateAPRFromAPY;
exports.sameLengthArrayEquals = sameLengthArrayEquals;
exports.getTokenBalanceFromAccountInfoLamports = getTokenBalanceFromAccountInfoLamports;
exports.bpsToPct = bpsToPct;
exports.truncateDecimals = truncateDecimals;
exports.decodeVaultName = decodeVaultName;
exports.pubkeyHashMapToJson = pubkeyHashMapToJson;
exports.toJson = toJson;
exports.assertNever = assertNever;
exports.orThrow = orThrow;
exports.blobEquals = blobEquals;
exports.roundNearest = roundNearest;
exports.getMedianSlotDurationInMsFromLastEpochs = getMedianSlotDurationInMsFromLastEpochs;
const utils_1 = require("../utils");
const decimal_js_1 = __importDefault(require("decimal.js"));
const axios_1 = __importDefault(require("axios"));
function getLatestRewardRate(rewardRates, slot) {
    return rewardRates
        .filter((rr) => slot >= rr.beginningSlot)
        .reduce((v1, v2) => (v1.beginningSlot > v2.beginningSlot ? v1 : v2), {
        beginningSlot: 0,
        rewardRate: '0',
    });
}
const calculateNewScore = (rewardStat, pool, rewardRate, endSlot, startSlot) => {
    const { balance, debt, score } = pool;
    const { rewardsPerShare, totalBalance } = rewardStat;
    const oldDebt = new decimal_js_1.default(debt);
    const oldScore = new decimal_js_1.default(score);
    const oldRewardsPerShare = new decimal_js_1.default(rewardsPerShare);
    const oldBalance = new decimal_js_1.default(balance);
    const totalBalanceVal = new decimal_js_1.default(totalBalance);
    const newRewardsPerShare = !totalBalanceVal.isZero()
        ? oldRewardsPerShare.plus(new decimal_js_1.default(endSlot)
            .minus(new decimal_js_1.default(startSlot.toString()))
            .times(new decimal_js_1.default(rewardRate))
            .div(totalBalanceVal)
            .div(new decimal_js_1.default(utils_1.SLOTS_PER_YEAR)))
        : new decimal_js_1.default(0);
    return oldScore.plus(newRewardsPerShare.times(oldBalance).minus(oldDebt));
};
exports.calculateNewScore = calculateNewScore;
const estimateCurrentScore = (rewardStat, rewardScore, mostRecentSlot, mostRecentSlotTime) => {
    const { lastSlot, rewardRates } = rewardStat;
    const estimatedCurrentSlot = mostRecentSlot + utils_1.SLOTS_PER_SECOND * (Date.now() / 1000 - mostRecentSlotTime);
    const { rewardRate } = getLatestRewardRate(rewardRates, estimatedCurrentSlot);
    const currentScore = (0, exports.calculateNewScore)(rewardStat, rewardScore, rewardRate, estimatedCurrentSlot, lastSlot);
    return currentScore;
};
exports.estimateCurrentScore = estimateCurrentScore;
const interpolate = (x, x0, x1, y0, y1) => {
    if (x > x1) {
        throw 'Cannot do extrapolation';
    }
    return y0 + ((x - x0) * (y1 - y0)) / (x1 - x0);
};
exports.interpolate = interpolate;
const getBorrowRate = (currentUtilization, curve) => {
    let [x0, y0, x1, y1] = [0, 0, 0, 0];
    if (curve.length < 2) {
        throw 'Invalid borrow rate curve, only one point';
    }
    if (currentUtilization > 1) {
        currentUtilization = 1;
    }
    for (let i = 1; i < curve.length; i++) {
        const [pointUtilization, pointRate] = curve[i];
        if (pointUtilization === currentUtilization) {
            return pointRate;
        }
        if (currentUtilization <= pointUtilization) {
            x0 = curve[i - 1][0];
            y0 = curve[i - 1][1];
            x1 = curve[i][0];
            y1 = curve[i][1];
            break;
        }
    }
    if (x0 === 0 && y0 === 0 && x1 === 0 && y1 === 0) {
        console.log('All are 0');
        throw 'Invalid borrow rate curve, could not identify the interpolation points.';
    }
    if (x0 >= x1 || y0 > y1) {
        console.log('(x0, y0), (x1, y1)', x0, y0, x1, y1);
        throw 'Invalid borrow rate curve, curve is not uniformly increasing';
    }
    return (0, exports.interpolate)(currentUtilization, x0, x1, y0, y1);
};
exports.getBorrowRate = getBorrowRate;
const parseTokenSymbol = (tokenSymbol) => {
    return String.fromCharCode(...tokenSymbol.filter((x) => x > 0));
};
exports.parseTokenSymbol = parseTokenSymbol;
function parseZeroPaddedUtf8(utf8Array) {
    for (let last = utf8Array.length - 1; last >= 0; last--) {
        const trailing_zero = utf8Array[last];
        if (trailing_zero != 0) {
            const encoding = new Uint8Array(last + 1);
            for (let i = 0; i <= last; i++) {
                encoding[i] = utf8Array[i];
            }
            return new TextDecoder().decode(encoding);
        }
    }
    return '';
}
function renderZeroPaddedUtf8(str, utf8ArrayLength) {
    const encoding = new TextEncoder().encode(str);
    const result = new Array(utf8ArrayLength);
    for (let i = 0; i < result.length; i++) {
        result[i] = i < encoding.length ? encoding[i] : 0;
    }
    return result;
}
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
function numberToLamportsDecimal(amount, decimals) {
    const factor = 10 ** decimals;
    return new decimal_js_1.default(amount).mul(factor);
}
function lamportsToNumberDecimal(amount, decimals) {
    const factor = 10 ** decimals;
    return new decimal_js_1.default(amount).div(factor);
}
function lamportsToDecimal(amount, decimals) {
    const factor = new decimal_js_1.default(10).pow(decimals);
    return new decimal_js_1.default(amount).div(factor);
}
const isSolMint = (mint) => {
    return utils_1.WRAPPED_SOL_MINT === mint;
};
exports.isSolMint = isSolMint;
const valueOrZero = (value) => {
    const zero = new decimal_js_1.default(0);
    if (value.isNaN() || !value.isFinite()) {
        return zero;
    }
    else {
        return value;
    }
};
exports.valueOrZero = valueOrZero;
const isEmptyObject = (obj) => {
    return Object.keys(obj).length === 0 && obj.constructor === Object;
};
exports.isEmptyObject = isEmptyObject;
const positiveOrZero = (value) => {
    const zero = new decimal_js_1.default(0);
    return decimal_js_1.default.max(value, zero);
};
exports.positiveOrZero = positiveOrZero;
function calculateAPYFromAPR(apr) {
    const apy = new decimal_js_1.default(1).plus(new decimal_js_1.default(apr).dividedBy(utils_1.SLOTS_PER_YEAR)).toNumber() ** utils_1.SLOTS_PER_YEAR - 1;
    return apy;
}
function calculateAPRFromAPY(apy) {
    return new decimal_js_1.default(apy)
        .plus(1)
        .pow(1 / utils_1.SLOTS_PER_YEAR)
        .minus(1)
        .times(utils_1.SLOTS_PER_YEAR);
}
function sameLengthArrayEquals(left, right) {
    if (left.length != right.length) {
        throw new Error(`Not same length: ${left.length} != ${right.length}`);
    }
    return left.every((value, index) => {
        const other = right[index];
        if (value != null && typeof value.eq === 'function') {
            return value.eq(other);
        }
        return value === other;
    });
}
function getTokenBalanceFromAccountInfoLamports(token) {
    return new decimal_js_1.default(token.data.amount.toString());
}
function bpsToPct(bps) {
    return bps.div(100);
}
/**
 * Truncate ( not round ) number to keep up to max amount of decimals
 * @param num
 * @param maxDecimals
 */
function truncateDecimals(num, maxDecimals) {
    const factor = new decimal_js_1.default(10).pow(maxDecimals);
    return new decimal_js_1.default(num).times(factor).floor().dividedBy(factor);
}
/**Convert an u8 array to a string */
function decodeVaultName(token) {
    const maxArray = new Uint8Array(token);
    let s = new TextDecoder().decode(maxArray);
    // Remove trailing zeros and spaces
    s = s.replace(/[\0 ]+$/, '');
    return s;
}
function pubkeyHashMapToJson(map) {
    const obj = {};
    map.forEach((value, key) => {
        obj[key] = value.toString();
    });
    return obj;
}
function toJson(object, inline = false) {
    const replacer = (key, value) => (typeof value === 'bigint' ? value.toString() : value);
    return inline ? JSON.stringify(object, replacer) : JSON.stringify(object, replacer, 2);
}
function assertNever(x) {
    throw new Error('Unexpected object: ' + x);
}
function orThrow(message) {
    throw new Error(message);
}
function blobEquals(left, right) {
    if (left.length !== right.length) {
        return false;
    }
    for (let i = 0; i < left.length; ++i) {
        if (left[i] !== right[i]) {
            return false;
        }
    }
    return true;
}
/**
 * Returns an integer {@link Decimal} nearest to the given one.
 *
 * NOTE: the `Decimal.round()` should actually be called `.trunc()` (by default, it uses floor rounding). In most cases,
 * we prefer the traditional behavior (as `Math.round()`).
 */
function roundNearest(decimal) {
    return decimal.toDecimalPlaces(0, decimal_js_1.default.ROUND_HALF_CEIL);
}
/**
 * Fetch median slot duration in milliseconds from the last 10 epochs
 */
async function getMedianSlotDurationInMsFromLastEpochs() {
    const response = await axios_1.default.get('https://api.kamino.finance/slots/duration');
    return response.data.recentSlotDurationInMs;
}
//# sourceMappingURL=utils.js.map