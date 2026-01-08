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
exports.OracleInitParams = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class OracleInitParams {
    name;
    metadata;
    stateBump;
    oracleBump;
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.stateBump = fields.stateBump;
        this.oracleBump = fields.oracleBump;
    }
    static layout(property) {
        return borsh.struct([
            borsh.vecU8("name"),
            borsh.vecU8("metadata"),
            borsh.u8("stateBump"),
            borsh.u8("oracleBump"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new OracleInitParams({
            name: new Uint8Array(obj.name.buffer, obj.name.byteOffset, obj.name.length),
            metadata: new Uint8Array(obj.metadata.buffer, obj.metadata.byteOffset, obj.metadata.length),
            stateBump: obj.stateBump,
            oracleBump: obj.oracleBump,
        });
    }
    static toEncodable(fields) {
        return {
            name: Buffer.from(fields.name.buffer, fields.name.byteOffset, fields.name.length),
            metadata: Buffer.from(fields.metadata.buffer, fields.metadata.byteOffset, fields.metadata.length),
            stateBump: fields.stateBump,
            oracleBump: fields.oracleBump,
        };
    }
    toJSON() {
        return {
            name: Array.from(this.name.values()),
            metadata: Array.from(this.metadata.values()),
            stateBump: this.stateBump,
            oracleBump: this.oracleBump,
        };
    }
    static fromJSON(obj) {
        return new OracleInitParams({
            name: Uint8Array.from(obj.name),
            metadata: Uint8Array.from(obj.metadata),
            stateBump: obj.stateBump,
            oracleBump: obj.oracleBump,
        });
    }
    toEncodable() {
        return OracleInitParams.toEncodable(this);
    }
}
exports.OracleInitParams = OracleInitParams;
//# sourceMappingURL=OracleInitParams.js.map