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
exports.DataSource = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class DataSource {
    chain;
    emitter;
    constructor(fields) {
        this.chain = fields.chain;
        this.emitter = fields.emitter;
    }
    static layout(property) {
        return borsh.struct([borsh.u16("chain"), (0, utils_1.borshAddress)("emitter")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new DataSource({
            chain: obj.chain,
            emitter: obj.emitter,
        });
    }
    static toEncodable(fields) {
        return {
            chain: fields.chain,
            emitter: fields.emitter,
        };
    }
    toJSON() {
        return {
            chain: this.chain,
            emitter: this.emitter,
        };
    }
    static fromJSON(obj) {
        return new DataSource({
            chain: obj.chain,
            emitter: (0, kit_1.address)(obj.emitter),
        });
    }
    toEncodable() {
        return DataSource.toEncodable(this);
    }
}
exports.DataSource = DataSource;
//# sourceMappingURL=DataSource.js.map