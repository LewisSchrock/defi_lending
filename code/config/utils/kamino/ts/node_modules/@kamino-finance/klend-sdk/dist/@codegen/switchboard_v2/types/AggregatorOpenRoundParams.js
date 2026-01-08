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
exports.AggregatorOpenRoundParams = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class AggregatorOpenRoundParams {
    stateBump;
    leaseBump;
    permissionBump;
    jitter;
    constructor(fields) {
        this.stateBump = fields.stateBump;
        this.leaseBump = fields.leaseBump;
        this.permissionBump = fields.permissionBump;
        this.jitter = fields.jitter;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u8("stateBump"),
            borsh.u8("leaseBump"),
            borsh.u8("permissionBump"),
            borsh.u8("jitter"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new AggregatorOpenRoundParams({
            stateBump: obj.stateBump,
            leaseBump: obj.leaseBump,
            permissionBump: obj.permissionBump,
            jitter: obj.jitter,
        });
    }
    static toEncodable(fields) {
        return {
            stateBump: fields.stateBump,
            leaseBump: fields.leaseBump,
            permissionBump: fields.permissionBump,
            jitter: fields.jitter,
        };
    }
    toJSON() {
        return {
            stateBump: this.stateBump,
            leaseBump: this.leaseBump,
            permissionBump: this.permissionBump,
            jitter: this.jitter,
        };
    }
    static fromJSON(obj) {
        return new AggregatorOpenRoundParams({
            stateBump: obj.stateBump,
            leaseBump: obj.leaseBump,
            permissionBump: obj.permissionBump,
            jitter: obj.jitter,
        });
    }
    toEncodable() {
        return AggregatorOpenRoundParams.toEncodable(this);
    }
}
exports.AggregatorOpenRoundParams = AggregatorOpenRoundParams;
//# sourceMappingURL=AggregatorOpenRoundParams.js.map