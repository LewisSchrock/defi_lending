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
exports.Full = exports.Partial = void 0;
exports.fromDecoded = fromDecoded;
exports.fromJSON = fromJSON;
exports.layout = layout;
const borsh = __importStar(require("@coral-xyz/borsh"));
class Partial {
    static discriminator = 0;
    static kind = "Partial";
    discriminator = 0;
    kind = "Partial";
    value;
    constructor(value) {
        this.value = {
            numSignatures: value.numSignatures,
        };
    }
    toJSON() {
        return {
            kind: "Partial",
            value: {
                numSignatures: this.value.numSignatures,
            },
        };
    }
    toEncodable() {
        return {
            Partial: {
                numSignatures: this.value.numSignatures,
            },
        };
    }
}
exports.Partial = Partial;
class Full {
    static discriminator = 1;
    static kind = "Full";
    discriminator = 1;
    kind = "Full";
    toJSON() {
        return {
            kind: "Full",
        };
    }
    toEncodable() {
        return {
            Full: {},
        };
    }
}
exports.Full = Full;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function fromDecoded(obj) {
    if (typeof obj !== "object") {
        throw new Error("Invalid enum object");
    }
    if ("Partial" in obj) {
        const val = obj["Partial"];
        return new Partial({
            numSignatures: val["numSignatures"],
        });
    }
    if ("Full" in obj) {
        return new Full();
    }
    throw new Error("Invalid enum object");
}
function fromJSON(obj) {
    switch (obj.kind) {
        case "Partial": {
            return new Partial({
                numSignatures: obj.value.numSignatures,
            });
        }
        case "Full": {
            return new Full();
        }
    }
}
function layout(property) {
    const ret = borsh.rustEnum([
        borsh.struct([borsh.u8("numSignatures")], "Partial"),
        borsh.struct([], "Full"),
    ]);
    if (property !== undefined) {
        return ret.replicate(property);
    }
    return ret;
}
//# sourceMappingURL=VerificationLevel.js.map