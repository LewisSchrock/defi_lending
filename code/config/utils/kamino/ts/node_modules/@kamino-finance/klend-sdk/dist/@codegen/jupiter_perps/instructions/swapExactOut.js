"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.layout = exports.DISCRIMINATOR = void 0;
exports.swapExactOut = swapExactOut;
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([250, 73, 101, 33, 38, 207, 75, 184]);
exports.layout = borsh.struct([
    types.SwapExactOutParams.layout("params"),
]);
function swapExactOut(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.owner.address, role: 3, signer: accounts.owner },
        { address: accounts.fundingAccount, role: 1 },
        { address: accounts.receivingAccount, role: 1 },
        { address: accounts.transferAuthority, role: 0 },
        { address: accounts.perpetuals, role: 0 },
        { address: accounts.pool, role: 1 },
        { address: accounts.receivingCustody, role: 1 },
        { address: accounts.receivingCustodyOracleAccount, role: 0 },
        { address: accounts.receivingCustodyTokenAccount, role: 1 },
        { address: accounts.dispensingCustody, role: 1 },
        { address: accounts.dispensingCustodyOracleAccount, role: 0 },
        { address: accounts.dispensingCustodyTokenAccount, role: 1 },
        { address: accounts.tokenProgram, role: 0 },
        { address: accounts.eventAuthority, role: 0 },
        { address: accounts.program, role: 0 },
        ...remainingAccounts,
    ];
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        params: types.SwapExactOutParams.toEncodable(args.params),
    }, buffer);
    const data = Buffer.concat([exports.DISCRIMINATOR, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=swapExactOut.js.map