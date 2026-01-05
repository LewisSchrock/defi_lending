import { Instruction } from '@solana/kit';
export declare function getPriorityFeeAndCuIxs({ priorityFeeMultiplier, computeUnits, }: {
    priorityFeeMultiplier: number;
    computeUnits?: number;
}): Instruction[];
export declare function removeComputeBudgetProgramInstructions(ixs: Instruction[]): Instruction[];
//# sourceMappingURL=priorityFee.d.ts.map