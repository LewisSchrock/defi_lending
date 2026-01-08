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
exports.layout = void 0;
exports.vrfCloseAction = vrfCloseAction;
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.layout = borsh.struct([types.VrfCloseParams.layout("params")]);
function vrfCloseAction(args, accounts, programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.authority.address,
            role: 2,
            signer: accounts.authority,
        },
        { address: accounts.vrf, role: 1 },
        { address: accounts.permission, role: 1 },
        { address: accounts.oracleQueue, role: 0 },
        { address: accounts.queueAuthority, role: 0 },
        { address: accounts.programState, role: 0 },
        { address: accounts.escrow, role: 1 },
        { address: accounts.solDest, role: 0 },
        { address: accounts.escrowDest, role: 1 },
        { address: accounts.tokenProgram, role: 0 },
    ];
    const identifier = Buffer.from([97, 172, 124, 16, 175, 10, 246, 147]);
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        params: types.VrfCloseParams.toEncodable(args.params),
    }, buffer);
    const data = Buffer.concat([identifier, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=vrfCloseAction.js.map