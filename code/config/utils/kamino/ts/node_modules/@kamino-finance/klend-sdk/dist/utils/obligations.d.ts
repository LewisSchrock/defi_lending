import { Address, Commitment, Rpc, Slot } from '@solana/kit';
import { KaminoMarket, KaminoMarketRpcApi, KaminoObligation } from '../classes';
export declare function getUserObligationsInMarkets(rpc: Rpc<KaminoMarketRpcApi>, user: Address, markets: Map<Address, KaminoMarket>, slot: Slot, commitment?: Commitment, programId?: Address): Promise<KaminoObligation[]>;
//# sourceMappingURL=obligations.d.ts.map