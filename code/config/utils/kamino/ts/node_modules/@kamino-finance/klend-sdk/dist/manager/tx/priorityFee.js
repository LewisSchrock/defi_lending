"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getPriorityFeeAndCuIxs = getPriorityFeeAndCuIxs;
exports.removeComputeBudgetProgramInstructions = removeComputeBudgetProgramInstructions;
const compute_budget_1 = require("@solana-program/compute-budget");
const microLamport = 10 ** 6; // 1 lamport
function getPriorityFeeAndCuIxs({ priorityFeeMultiplier, computeUnits = 200_000, }) {
    const microLamportsPrioritizationFee = microLamport / computeUnits;
    return [
        (0, compute_budget_1.getSetComputeUnitLimitInstruction)({ units: computeUnits }),
        (0, compute_budget_1.getSetComputeUnitPriceInstruction)({
            microLamports: Math.round(microLamportsPrioritizationFee * priorityFeeMultiplier),
        }),
    ];
}
function removeComputeBudgetProgramInstructions(ixs) {
    const filteredIxs = ixs.filter((ix) => {
        if (ix.programAddress === compute_budget_1.COMPUTE_BUDGET_PROGRAM_ADDRESS) {
            return false;
        }
        return true;
    });
    return filteredIxs;
}
//# sourceMappingURL=priorityFee.js.map