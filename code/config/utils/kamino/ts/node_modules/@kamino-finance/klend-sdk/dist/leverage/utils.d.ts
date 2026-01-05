import { KaminoReserve } from '../classes';
import { Address, GetAccountInfoApi, Rpc, GetTokenAccountBalanceApi } from '@solana/kit';
import Decimal from 'decimal.js';
export declare const getExpectedTokenBalanceAfterBorrow: (rpc: Rpc<GetAccountInfoApi & GetTokenAccountBalanceApi>, mint: Address, owner: Address, amountToBorrowLamports: Decimal, amountToBorrowMintDecimals: number) => Promise<Decimal>;
export declare const isBorrowingEnabled: (reserve: KaminoReserve) => boolean;
//# sourceMappingURL=utils.d.ts.map