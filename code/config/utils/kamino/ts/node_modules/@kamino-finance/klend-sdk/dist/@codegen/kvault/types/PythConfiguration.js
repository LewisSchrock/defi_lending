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
exports.PythConfiguration = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class PythConfiguration {
    /** Pubkey of the base price feed (disabled if `null` or `default`) */
    price;
    constructor(fields) {
        this.price = fields.price;
    }
    static layout(property) {
        return borsh.struct([(0, utils_1.borshAddress)("price")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PythConfiguration({
            price: obj.price,
        });
    }
    static toEncodable(fields) {
        return {
            price: fields.price,
        };
    }
    toJSON() {
        return {
            price: this.price,
        };
    }
    static fromJSON(obj) {
        return new PythConfiguration({
            price: (0, kit_1.address)(obj.price),
        });
    }
    toEncodable() {
        return PythConfiguration.toEncodable(this);
    }
}
exports.PythConfiguration = PythConfiguration;
//# sourceMappingURL=PythConfiguration.js.map