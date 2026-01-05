"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.walletIsSquadsMultisig = walletIsSquadsMultisig;
exports.getSquadsMultisigAdminsAndThreshold = getSquadsMultisigAdminsAndThreshold;
const SQUADS_API_BASE_URL = 'https://4fnetmviidiqkjzenwxe66vgoa0soerr.lambda-url.us-east-1.on.aws';
async function walletIsSquadsMultisig(wallet) {
    const response = await fetch(`${SQUADS_API_BASE_URL}/isSquad/${wallet}`);
    const data = await response.json();
    const squadsResponse = data;
    return squadsResponse.isSquad;
}
async function getSquadsMultisigAdminsAndThreshold(wallet) {
    const response = await fetch(`${SQUADS_API_BASE_URL}/multisig/${wallet}`);
    const data = await response.json();
    try {
        const squadsResponse = data;
        return {
            adminsNumber: squadsResponse.account.members.length,
            threshold: squadsResponse.account.threshold,
        };
    }
    catch (e) {
        const squadsResponse = data;
        return {
            adminsNumber: squadsResponse.keys.length,
            threshold: squadsResponse.threshold,
        };
    }
}
//# sourceMappingURL=multisig.js.map