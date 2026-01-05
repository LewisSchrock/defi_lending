import Decimal from 'decimal.js';
import { Address } from '@solana/kit';
export interface ReserveAllocationOverview {
    targetWeight: Decimal;
    tokenAllocationCap: Decimal;
    ctokenAllocation: Decimal;
}
export interface VaultAllocationResult {
    targetUnallocatedAmount: Decimal;
    targetReservesAllocation: Map<Address, Decimal>;
}
/**
 * Computes the allocation of vault funds across reserves based on weights and caps
 * @param vaultAUM - Total AUM of the vault, in tokens
 * @param vaultUnallocatedWeight - Weight for unallocated funds
 * @param vaultUnallocatedCap - Maximum amount that can remain unallocated
 * @param initialVaultAllocations - Map of reserve addresses to their allocation configurations
 * @param vaultTokenDecimals - The number of decimals of the vault token, needed to compute the min amount
 * @returns Object containing target unallocated amount and target allocations per reserve, in tokens
 */
export declare function computeReservesAllocation(vaultAUM: Decimal, vaultUnallocatedWeight: Decimal, vaultUnallocatedCap: Decimal, initialVaultAllocations: Map<Address, ReserveAllocationOverview>, vaultTokenDecimals: number): VaultAllocationResult;
//# sourceMappingURL=vaultAllocation.d.ts.map