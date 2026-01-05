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
exports.liquidatePosition = liquidatePosition;
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([187, 74, 229, 149, 102, 81, 221, 68]);
exports.layout = borsh.struct([
    types.LiquidatePositionParams.layout("params"),
]);
function liquidatePosition(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.signer.address, role: 3, signer: accounts.signer },
        { address: accounts.receivingAccount, role: 1 },
        { address: accounts.rewardReceivingAccount, role: 1 },
        { address: accounts.transferAuthority, role: 0 },
        { address: accounts.perpetuals, role: 0 },
        { address: accounts.pool, role: 1 },
        { address: accounts.position, role: 1 },
        { address: accounts.custody, role: 1 },
        { address: accounts.custodyOracleAccount, role: 0 },
        { address: accounts.collateralCustody, role: 1 },
        { address: accounts.collateralCustodyOracleAccount, role: 0 },
        { address: accounts.collateralCustodyTokenAccount, role: 1 },
        { address: accounts.tokenProgram, role: 0 },
        { address: accounts.eventAuthority, role: 0 },
        { address: accounts.program, role: 0 },
        ...remainingAccounts,
    ];
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        params: types.LiquidatePositionParams.toEncodable(args.params),
    }, buffer);
    const data = Buffer.concat([exports.DISCRIMINATOR, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=liquidatePosition.js.map