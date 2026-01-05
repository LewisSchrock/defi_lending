import { Address, Rpc, Slot, SolanaRpcApi } from '@solana/kit';
import { Decimal } from 'decimal.js';
import { FarmIncentives, Farms } from '@kamino-finance/farms-sdk';
import { Reserve } from '../@codegen/klend/accounts';
export interface ReserveIncentives {
    collateralFarmIncentives: FarmIncentives;
    debtFarmIncentives: FarmIncentives;
}
export declare function getReserveFarmRewardsAPY(rpc: Rpc<SolanaRpcApi>, recentSlotDurationMs: number, reserve: Address, reserveLiquidityTokenPrice: Decimal, kaminoLendProgramId: Address, farmsClient: Farms, slot: Slot, reserveState?: Reserve, tokensPrices?: Map<Address, Decimal>): Promise<ReserveIncentives>;
//# sourceMappingURL=farmUtils.d.ts.map