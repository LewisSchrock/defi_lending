"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getReserveFarmRewardsAPY = getReserveFarmRewardsAPY;
const apy_1 = require("@kamino-finance/farms-sdk/dist/utils/apy");
const farms_sdk_1 = require("@kamino-finance/farms-sdk");
const accounts_1 = require("../@codegen/klend/accounts");
const lib_1 = require("../lib");
async function getReserveFarmRewardsAPY(rpc, recentSlotDurationMs, reserve, reserveLiquidityTokenPrice, kaminoLendProgramId, farmsClient, slot, reserveState, tokensPrices) {
    const reserveIncentives = {
        collateralFarmIncentives: {
            incentivesStats: [],
            totalIncentivesApy: 0,
        },
        debtFarmIncentives: {
            incentivesStats: [],
            totalIncentivesApy: 0,
        },
    };
    const reserveAccount = reserveState ? reserveState : await accounts_1.Reserve.fetch(rpc, reserve, kaminoLendProgramId);
    if (!reserveAccount) {
        throw new Error(`Reserve ${reserve} not found`);
    }
    const kaminoReserve = await lib_1.KaminoReserve.initializeFromAddress(reserve, rpc, recentSlotDurationMs, reserveAccount);
    const farmCollateral = kaminoReserve.state.farmCollateral;
    const farmDebt = kaminoReserve.state.farmDebt;
    const stakedTokenMintDecimals = kaminoReserve.getMintDecimals();
    const reserveCtokenPrice = reserveLiquidityTokenPrice.div(kaminoReserve.getEstimatedCollateralExchangeRate(slot, 0));
    if (farmCollateral !== farms_sdk_1.DEFAULT_PUBLIC_KEY) {
        const farmIncentivesCollateral = await (0, apy_1.getFarmIncentives)(farmsClient, farmCollateral, reserveCtokenPrice, stakedTokenMintDecimals, tokensPrices);
        reserveIncentives.collateralFarmIncentives = farmIncentivesCollateral;
    }
    if (farmDebt !== farms_sdk_1.DEFAULT_PUBLIC_KEY) {
        const farmIncentivesDebt = await (0, apy_1.getFarmIncentives)(farmsClient, farmDebt, reserveLiquidityTokenPrice, stakedTokenMintDecimals, tokensPrices);
        reserveIncentives.debtFarmIncentives = farmIncentivesDebt;
    }
    return reserveIncentives;
}
//# sourceMappingURL=farmUtils.js.map