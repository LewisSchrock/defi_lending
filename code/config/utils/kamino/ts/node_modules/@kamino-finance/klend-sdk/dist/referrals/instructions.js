"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getDeleteReferrerStateAndShortUrlIxs = exports.getInitReferrerStateAndShortUrlIxs = exports.getInitAllReferrerTokenStateIxs = void 0;
const utils_1 = require("../utils");
const lib_1 = require("../lib");
const sysvars_1 = require("@solana/sysvars");
const system_1 = require("@solana-program/system");
const getInitAllReferrerTokenStateIxs = async ({ payer, kaminoMarket, referrer = payer.address, }) => {
    if (referrer === utils_1.DEFAULT_PUBLIC_KEY) {
        throw new Error('Referrer not set');
    }
    await kaminoMarket.loadReserves();
    const initReferrerTokenStateIxs = [];
    const tokenStatesToCreate = [];
    const reserves = kaminoMarket.getReserves();
    const referrerTokenStates = await Promise.all(reserves.map(async (reserve) => {
        return await (0, utils_1.referrerTokenStatePda)(referrer, reserve.address, kaminoMarket.programId);
    }));
    const uniqueReferrerTokenStates = [...new Set(referrerTokenStates)];
    const accounts = await kaminoMarket.getRpc().getMultipleAccounts(uniqueReferrerTokenStates).send();
    for (let i = 0; i < uniqueReferrerTokenStates.length; i++) {
        if (accounts.value[i] !== null) {
            tokenStatesToCreate.push([uniqueReferrerTokenStates[i], reserves[i].address]);
        }
    }
    tokenStatesToCreate.forEach(([referrerTokenStateAddress, reserveAddress]) => {
        const initReferrerTokenStateIx = (0, lib_1.initReferrerTokenState)({
            lendingMarket: kaminoMarket.getAddress(),
            payer,
            reserve: reserveAddress,
            referrer,
            referrerTokenState: referrerTokenStateAddress,
            rent: sysvars_1.SYSVAR_RENT_ADDRESS,
            systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
        }, undefined, kaminoMarket.programId);
        initReferrerTokenStateIxs.push(initReferrerTokenStateIx);
    });
    return initReferrerTokenStateIxs;
};
exports.getInitAllReferrerTokenStateIxs = getInitAllReferrerTokenStateIxs;
const getInitReferrerStateAndShortUrlIxs = async ({ referrer, shortUrl, programId = lib_1.PROGRAM_ID, }) => {
    const [[referrerState], referrerShortUrl, [referrerUserMetadata]] = await Promise.all([
        (0, utils_1.referrerStatePda)(referrer.address, programId),
        (0, utils_1.shortUrlPda)(shortUrl, programId),
        (0, utils_1.userMetadataPda)(referrer.address, programId),
    ]);
    const initReferrerStateAndShortUrlIx = (0, lib_1.initReferrerStateAndShortUrl)({
        shortUrl: shortUrl,
    }, {
        referrer: referrer,
        referrerState,
        referrerShortUrl,
        referrerUserMetadata,
        rent: sysvars_1.SYSVAR_RENT_ADDRESS,
        systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
    }, undefined, programId);
    return initReferrerStateAndShortUrlIx;
};
exports.getInitReferrerStateAndShortUrlIxs = getInitReferrerStateAndShortUrlIxs;
// TODO: 1 thing left before adding program id
const getDeleteReferrerStateAndShortUrlIxs = async ({ referrer, rpc, programId = lib_1.PROGRAM_ID, }) => {
    const [referrerStateAddress] = await (0, utils_1.referrerStatePda)(referrer.address, programId);
    const referrerState = await lib_1.ReferrerState.fetch(rpc, referrerStateAddress, programId);
    return (0, lib_1.deleteReferrerStateAndShortUrl)({
        referrer: referrer,
        referrerState: referrerStateAddress,
        shortUrl: referrerState.shortUrl,
        rent: sysvars_1.SYSVAR_RENT_ADDRESS,
        systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
    }, undefined, programId);
};
exports.getDeleteReferrerStateAndShortUrlIxs = getDeleteReferrerStateAndShortUrlIxs;
//# sourceMappingURL=instructions.js.map