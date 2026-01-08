import { Address, Rpc, GetProgramAccountsApi, GetAccountInfoApi, GetProgramAccountsDatasizeFilter, GetProgramAccountsMemcmpFilter, Account } from '@solana/kit';
import { Buffer } from 'buffer';
import { DataSlice } from '@solana/rpc-types/dist/types/account-filters';
/**
 * Uses zstd compression when fetching all accounts owned by a program for a smaller response size
 * Uses axios instead of node-fetch to work around a bug in node-fetch that causes subsequent requests with different encoding to fail
 * @param rpc
 * @param programId
 * @param structSize - the size of the decompressed account data struct
 * @param filters
 * @param dataSlice
 */
export declare function getProgramAccounts(rpc: Rpc<GetProgramAccountsApi>, programId: Address, structSize: number, filters: (GetProgramAccountsDatasizeFilter | GetProgramAccountsMemcmpFilter)[], dataSlice?: DataSlice): Promise<Account<Buffer>[]>;
export declare function getAccountOwner(rpc: Rpc<GetAccountInfoApi>, address: Address): Promise<Address>;
//# sourceMappingURL=rpc.d.ts.map