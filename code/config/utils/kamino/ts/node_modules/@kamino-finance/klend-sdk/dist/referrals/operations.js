"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.isShortUrlAvailable = isShortUrlAvailable;
exports.getReferrerShortUrl = getReferrerShortUrl;
exports.getReferrerForShortUrl = getReferrerForShortUrl;
exports.getUserMetadatasByReferrer = getUserMetadatasByReferrer;
exports.getAllUserMetadatas = getAllUserMetadatas;
exports.getTotalUsersReferred = getTotalUsersReferred;
exports.getReferralsRanking = getReferralsRanking;
exports.getUserReferralRanking = getUserReferralRanking;
const kit_1 = require("@solana/kit");
const utils_1 = require("../utils");
const lib_1 = require("../lib");
const decimal_js_1 = __importDefault(require("decimal.js"));
/**
 * Check if short URL available - also checks if short URL is valid (ascii-alphanumeric plus '_' '-', max 32 chars)
 * @param connection
 * @param shortUrl
 * @param programId
 */
async function isShortUrlAvailable(connection, shortUrl, programId = lib_1.PROGRAM_ID) {
    if (shortUrl.length > 32) {
        return false;
    }
    if (!/^[a-zA-Z0-9-_]+$/.test(shortUrl)) {
        return false;
    }
    const shortUrlAddress = await (0, utils_1.shortUrlPda)(shortUrl, programId);
    const info = await (0, kit_1.fetchEncodedAccount)(connection, shortUrlAddress);
    return !info.exists;
}
/**
 * Get referrer short URL address and shortUrl
 * @param rpc
 * @param referrer
 * @param programId
 */
async function getReferrerShortUrl(rpc, referrer, programId = lib_1.PROGRAM_ID) {
    const [referrerStateAddress] = await (0, utils_1.referrerStatePda)(referrer, programId);
    const referrerState = await lib_1.ReferrerState.fetch(rpc, referrerStateAddress, programId);
    const shortUrlState = await lib_1.ShortUrl.fetch(rpc, referrerState.shortUrl, programId);
    const shortUrlAddress = referrerState ? referrerState.shortUrl : null;
    const shortUrl = shortUrlState ? shortUrlState.shortUrl : null;
    return [shortUrlAddress, shortUrl];
}
/**
 * Get referrer for a given Short URL
 * @param rpc
 * @param shortUrl
 * @param programId
 */
async function getReferrerForShortUrl(rpc, shortUrl, programId = lib_1.PROGRAM_ID) {
    const shortUrlAddress = await (0, utils_1.shortUrlPda)(shortUrl, programId);
    const shortUrlState = await lib_1.ShortUrl.fetch(rpc, shortUrlAddress, programId);
    return shortUrlState.referrer;
}
/**
 * Get referrer all UserMetadata user accounts linked to a given referrer
 * @param rpc
 * @param referrer
 * @param programId
 */
async function getUserMetadatasByReferrer(rpc, referrer, programId = lib_1.PROGRAM_ID) {
    const userMetadatas = await rpc
        .getProgramAccounts(programId, {
        filters: [
            {
                dataSize: BigInt(lib_1.UserMetadata.layout.span + 8),
            },
            {
                memcmp: {
                    offset: 8n,
                    bytes: referrer.toString(),
                    encoding: 'base58',
                },
            },
        ],
        encoding: 'base64',
    })
        .send();
    return userMetadatas.map((userMetadata) => {
        if (userMetadata.account.owner !== programId) {
            throw new Error("account doesn't belong to this program");
        }
        const userMetadataAccount = lib_1.UserMetadata.decode(Buffer.from(userMetadata.account.data[0], 'base64'));
        if (!userMetadataAccount) {
            throw Error('Could not parse obligation.');
        }
        return userMetadataAccount;
    });
}
/**
 * Get referrer all UserMetadata user accounts
 * @param rpc
 * @param referrer
 * @param programId
 */
async function getAllUserMetadatas(rpc, programId = lib_1.PROGRAM_ID) {
    const userMetadatas = await rpc
        .getProgramAccounts(programId, {
        filters: [
            {
                dataSize: BigInt(lib_1.UserMetadata.layout.span + 8),
            },
        ],
        encoding: 'base64',
    })
        .send();
    return userMetadatas.map((userMetadata) => {
        if (userMetadata.account.owner !== programId) {
            throw new Error("account doesn't belong to this program");
        }
        const userMetadataAccount = lib_1.UserMetadata.decode(Buffer.from(userMetadata.account.data[0], 'base64'));
        if (!userMetadataAccount) {
            throw Error('Could not parse obligation.');
        }
        return userMetadataAccount;
    });
}
/**
 * Get referrer all UserMetadata user accounts linked to a given referrer
 * @param rpc
 * @param referrer
 * @param programId
 */
async function getTotalUsersReferred(rpc, referrer, programId = lib_1.PROGRAM_ID) {
    const userMetadatas = await getUserMetadatasByReferrer(rpc, referrer, programId);
    return userMetadatas.length;
}
/**
 * Get ReferralRank array of all referrers ordered by how much they've earned in USD
 * @param rpc
 * @param kaminoMarket
 */
async function getReferralsRanking(rpc, kaminoMarket) {
    const referrersUsersReferred = new Map();
    // counting users referred for each referrer
    const userMetadatas = await getAllUserMetadatas(rpc, kaminoMarket.programId);
    for (const userMetadata of userMetadatas) {
        const referrer = userMetadata.referrer;
        const usersReferred = referrersUsersReferred.get(referrer);
        if (usersReferred) {
            referrersUsersReferred.set(referrer, usersReferred + 1);
        }
        else {
            referrersUsersReferred.set(referrer, 1);
        }
    }
    const referralsRankArray = [];
    for (const referrer of referrersUsersReferred.keys()) {
        const referrerTokenStates = await kaminoMarket.getAllReferrerFeesCumulative(referrer);
        let totalEarningsUsd = new decimal_js_1.default(0);
        // calculating earnings for each referrer
        for (const reserve of kaminoMarket.reserves.values()) {
            totalEarningsUsd = totalEarningsUsd.add(referrerTokenStates.get(reserve.getLiquidityMint()).mul(reserve.getOracleMarketPrice()));
        }
        referralsRankArray.push({
            referrer: (0, kit_1.address)(referrer),
            totalUsersReferred: referrersUsersReferred.get(referrer),
            totalEarningsUsd: totalEarningsUsd,
        });
    }
    referralsRankArray.sort((a, b) => {
        return b.totalEarningsUsd.comparedTo(a.totalEarningsUsd);
    });
    return referralsRankArray;
}
/**
 * Get ReferralRank array of all referrers ordered by how much they've earned in USD
 * @param connection
 * @param user
 * @param kaminoMarket
 */
async function getUserReferralRanking(connection, user, kaminoMarket) {
    const referralsRanking = await getReferralsRanking(connection, kaminoMarket);
    for (let index = 0; index < referralsRanking.length; index++) {
        if (user === referralsRanking[index].referrer) {
            return index + 1;
        }
    }
    return undefined;
}
//# sourceMappingURL=operations.js.map