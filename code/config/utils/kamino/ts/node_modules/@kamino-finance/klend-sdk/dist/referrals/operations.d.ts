import { Address, GetProgramAccountsApi, Rpc, GetAccountInfoApi } from '@solana/kit';
import { KaminoMarket } from '../classes';
import { UserMetadata } from '../lib';
import Decimal from 'decimal.js';
/**
 * Check if short URL available - also checks if short URL is valid (ascii-alphanumeric plus '_' '-', max 32 chars)
 * @param connection
 * @param shortUrl
 * @param programId
 */
export declare function isShortUrlAvailable(connection: Rpc<GetAccountInfoApi>, shortUrl: string, programId?: Address): Promise<boolean>;
/**
 * Get referrer short URL address and shortUrl
 * @param rpc
 * @param referrer
 * @param programId
 */
export declare function getReferrerShortUrl(rpc: Rpc<GetAccountInfoApi>, referrer: Address, programId?: Address): Promise<[Address | null, string | null]>;
/**
 * Get referrer for a given Short URL
 * @param rpc
 * @param shortUrl
 * @param programId
 */
export declare function getReferrerForShortUrl(rpc: Rpc<GetAccountInfoApi>, shortUrl: string, programId?: Address): Promise<Address>;
/**
 * Get referrer all UserMetadata user accounts linked to a given referrer
 * @param rpc
 * @param referrer
 * @param programId
 */
export declare function getUserMetadatasByReferrer(rpc: Rpc<GetProgramAccountsApi>, referrer: Address, programId?: Address): Promise<UserMetadata[]>;
/**
 * Get referrer all UserMetadata user accounts
 * @param rpc
 * @param referrer
 * @param programId
 */
export declare function getAllUserMetadatas(rpc: Rpc<GetProgramAccountsApi>, programId?: Address): Promise<UserMetadata[]>;
/**
 * Get referrer all UserMetadata user accounts linked to a given referrer
 * @param rpc
 * @param referrer
 * @param programId
 */
export declare function getTotalUsersReferred(rpc: Rpc<GetProgramAccountsApi>, referrer: Address, programId?: Address): Promise<number>;
export type ReferralRank = {
    referrer: Address;
    totalUsersReferred: number;
    totalEarningsUsd: Decimal;
};
/**
 * Get ReferralRank array of all referrers ordered by how much they've earned in USD
 * @param rpc
 * @param kaminoMarket
 */
export declare function getReferralsRanking(rpc: Rpc<GetProgramAccountsApi>, kaminoMarket: KaminoMarket): Promise<ReferralRank[]>;
/**
 * Get ReferralRank array of all referrers ordered by how much they've earned in USD
 * @param connection
 * @param user
 * @param kaminoMarket
 */
export declare function getUserReferralRanking(connection: Rpc<GetProgramAccountsApi>, user: Address, kaminoMarket: KaminoMarket): Promise<number | undefined>;
//# sourceMappingURL=operations.d.ts.map