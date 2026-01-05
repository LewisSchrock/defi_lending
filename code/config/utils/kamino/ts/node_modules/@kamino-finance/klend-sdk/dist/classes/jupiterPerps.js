"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getJLPApr = getJLPApr;
const Pool_1 = require("../@codegen/jupiter_perps/accounts/Pool");
async function getJLPApr(connection, poolAddress) {
    const jlpPool = await Pool_1.Pool.fetch(connection, poolAddress);
    if (!jlpPool) {
        throw new Error('JLP pool not found');
    }
    const poolApr = jlpPool.poolApr;
    return poolApr.feeAprBps.toNumber() / 100;
}
//# sourceMappingURL=jupiterPerps.js.map