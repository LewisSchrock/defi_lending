"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.processTx = processTx;
const tx_1 = require("./tx");
const simulate_1 = require("./simulate");
const multisig_1 = require("./multisig");
const CliEnv_1 = require("./CliEnv");
async function processTx(c, payer, ixs, mode, luts = []) {
    switch (mode) {
        case 'execute':
            await (0, tx_1.sendAndConfirmTx)(c, payer, ixs, luts);
            break;
        case 'simulate':
            await (0, simulate_1.printSimulateTx)(c, payer, ixs, luts);
            break;
        case 'multisig':
            await (0, multisig_1.printMultisigTx)(payer, ixs, luts);
            break;
        case 'print':
            break;
        default:
            throw new Error(`Unknown tx mode ${mode}, valid options: ${CliEnv_1.sendTxModes.join('|')}`);
    }
}
//# sourceMappingURL=processor.js.map