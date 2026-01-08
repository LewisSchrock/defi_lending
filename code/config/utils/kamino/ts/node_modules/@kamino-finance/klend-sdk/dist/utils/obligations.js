"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getUserObligationsInMarkets = getUserObligationsInMarkets;
const kit_1 = require("@solana/kit");
const classes_1 = require("../classes");
const programId_1 = require("../@codegen/klend/programId");
const accounts_1 = require("../@codegen/klend/accounts");
async function getUserObligationsInMarkets(rpc, user, markets, slot, commitment = 'processed', programId = programId_1.PROGRAM_ID) {
    const obligations = await rpc
        .getProgramAccounts(programId, {
        filters: [
            {
                dataSize: BigInt(accounts_1.Obligation.layout.span + 8),
            },
            {
                memcmp: {
                    offset: 0n,
                    bytes: (0, kit_1.getBase58Decoder)().decode(accounts_1.Obligation.discriminator),
                    encoding: 'base58',
                },
            },
            {
                memcmp: {
                    offset: 64n,
                    bytes: user.toString(),
                    encoding: 'base58',
                },
            },
        ],
        encoding: 'base64',
        commitment,
    })
        .send();
    const collateralExchangeRates = new Map();
    const cumulativeBorrowRates = new Map();
    const kaminoObligations = [];
    for (const obligation of obligations) {
        if (obligation.account.owner !== programId) {
            throw new Error(`Account ${obligation.account.owner} doesn't belong to this program ${programId}`);
        }
        const obligationAccount = accounts_1.Obligation.decode(Buffer.from(obligation.account.data[0], 'base64'));
        if (!obligationAccount) {
            throw Error('Could not parse obligation.');
        }
        const market = markets.get(obligationAccount.lendingMarket);
        if (!market) {
            continue;
        }
        classes_1.KaminoObligation.addRatesForObligation(market, obligationAccount, collateralExchangeRates, cumulativeBorrowRates, slot);
        kaminoObligations.push(new classes_1.KaminoObligation(market, obligation.pubkey, obligationAccount, collateralExchangeRates, cumulativeBorrowRates));
    }
    return kaminoObligations;
}
//# sourceMappingURL=obligations.js.map