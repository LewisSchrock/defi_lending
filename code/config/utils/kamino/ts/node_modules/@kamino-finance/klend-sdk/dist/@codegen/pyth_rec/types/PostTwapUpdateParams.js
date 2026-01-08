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
exports.PostTwapUpdateParams = void 0;
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class PostTwapUpdateParams {
    startMerklePriceUpdate;
    endMerklePriceUpdate;
    treasuryId;
    constructor(fields) {
        this.startMerklePriceUpdate = new types.MerklePriceUpdate({
            ...fields.startMerklePriceUpdate,
        });
        this.endMerklePriceUpdate = new types.MerklePriceUpdate({
            ...fields.endMerklePriceUpdate,
        });
        this.treasuryId = fields.treasuryId;
    }
    static layout(property) {
        return borsh.struct([
            types.MerklePriceUpdate.layout("startMerklePriceUpdate"),
            types.MerklePriceUpdate.layout("endMerklePriceUpdate"),
            borsh.u8("treasuryId"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PostTwapUpdateParams({
            startMerklePriceUpdate: types.MerklePriceUpdate.fromDecoded(obj.startMerklePriceUpdate),
            endMerklePriceUpdate: types.MerklePriceUpdate.fromDecoded(obj.endMerklePriceUpdate),
            treasuryId: obj.treasuryId,
        });
    }
    static toEncodable(fields) {
        return {
            startMerklePriceUpdate: types.MerklePriceUpdate.toEncodable(fields.startMerklePriceUpdate),
            endMerklePriceUpdate: types.MerklePriceUpdate.toEncodable(fields.endMerklePriceUpdate),
            treasuryId: fields.treasuryId,
        };
    }
    toJSON() {
        return {
            startMerklePriceUpdate: this.startMerklePriceUpdate.toJSON(),
            endMerklePriceUpdate: this.endMerklePriceUpdate.toJSON(),
            treasuryId: this.treasuryId,
        };
    }
    static fromJSON(obj) {
        return new PostTwapUpdateParams({
            startMerklePriceUpdate: types.MerklePriceUpdate.fromJSON(obj.startMerklePriceUpdate),
            endMerklePriceUpdate: types.MerklePriceUpdate.fromJSON(obj.endMerklePriceUpdate),
            treasuryId: obj.treasuryId,
        });
    }
    toEncodable() {
        return PostTwapUpdateParams.toEncodable(this);
    }
}
exports.PostTwapUpdateParams = PostTwapUpdateParams;
//# sourceMappingURL=PostTwapUpdateParams.js.map