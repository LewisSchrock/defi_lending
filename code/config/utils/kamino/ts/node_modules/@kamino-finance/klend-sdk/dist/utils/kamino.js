"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isKtoken = isKtoken;
const kit_1 = require("@solana/kit");
const token_2022_1 = require("@solana-program/token-2022");
const buffer_1 = require("buffer");
const addressEncoder = (0, kit_1.getAddressEncoder)();
async function isKtoken(mint, kamino) {
    const [expectedMintAuthority] = await (0, kit_1.getProgramDerivedAddress)({
        seeds: [buffer_1.Buffer.from('authority'), addressEncoder.encode(mint)],
        programAddress: kamino.getProgramID(),
    });
    const mintState = await (0, token_2022_1.fetchMint)(kamino.getConnection(), mint);
    return (0, kit_1.isSome)(mintState.data.mintAuthority) && mintState.data.mintAuthority.value === expectedMintAuthority;
}
//# sourceMappingURL=kamino.js.map