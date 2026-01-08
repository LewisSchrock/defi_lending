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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Name = exports.ElevationGroup = exports.Pubkey = exports.U128 = exports.U64 = exports.U16 = exports.U8Array = exports.U8 = exports.Bool = void 0;
exports.fromDecoded = fromDecoded;
exports.fromJSON = fromJSON;
exports.layout = layout;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class Bool {
    static discriminator = 0;
    static kind = "Bool";
    discriminator = 0;
    kind = "Bool";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "Bool",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            Bool: {
                _0: this.value[0],
            },
        };
    }
}
exports.Bool = Bool;
class U8 {
    static discriminator = 1;
    static kind = "U8";
    discriminator = 1;
    kind = "U8";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "U8",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            U8: {
                _0: this.value[0],
            },
        };
    }
}
exports.U8 = U8;
class U8Array {
    static discriminator = 2;
    static kind = "U8Array";
    discriminator = 2;
    kind = "U8Array";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "U8Array",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            U8Array: {
                _0: this.value[0],
            },
        };
    }
}
exports.U8Array = U8Array;
class U16 {
    static discriminator = 3;
    static kind = "U16";
    discriminator = 3;
    kind = "U16";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "U16",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            U16: {
                _0: this.value[0],
            },
        };
    }
}
exports.U16 = U16;
class U64 {
    static discriminator = 4;
    static kind = "U64";
    discriminator = 4;
    kind = "U64";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "U64",
            value: [this.value[0].toString()],
        };
    }
    toEncodable() {
        return {
            U64: {
                _0: this.value[0],
            },
        };
    }
}
exports.U64 = U64;
class U128 {
    static discriminator = 5;
    static kind = "U128";
    discriminator = 5;
    kind = "U128";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "U128",
            value: [this.value[0].toString()],
        };
    }
    toEncodable() {
        return {
            U128: {
                _0: this.value[0],
            },
        };
    }
}
exports.U128 = U128;
class Pubkey {
    static discriminator = 6;
    static kind = "Pubkey";
    discriminator = 6;
    kind = "Pubkey";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "Pubkey",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            Pubkey: {
                _0: this.value[0],
            },
        };
    }
}
exports.Pubkey = Pubkey;
class ElevationGroup {
    static discriminator = 7;
    static kind = "ElevationGroup";
    discriminator = 7;
    kind = "ElevationGroup";
    value;
    constructor(value) {
        this.value = [new types.ElevationGroup({ ...value[0] })];
    }
    toJSON() {
        return {
            kind: "ElevationGroup",
            value: [this.value[0].toJSON()],
        };
    }
    toEncodable() {
        return {
            ElevationGroup: {
                _0: types.ElevationGroup.toEncodable(this.value[0]),
            },
        };
    }
}
exports.ElevationGroup = ElevationGroup;
class Name {
    static discriminator = 8;
    static kind = "Name";
    discriminator = 8;
    kind = "Name";
    value;
    constructor(value) {
        this.value = [value[0]];
    }
    toJSON() {
        return {
            kind: "Name",
            value: [this.value[0]],
        };
    }
    toEncodable() {
        return {
            Name: {
                _0: this.value[0],
            },
        };
    }
}
exports.Name = Name;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function fromDecoded(obj) {
    if (typeof obj !== "object") {
        throw new Error("Invalid enum object");
    }
    if ("Bool" in obj) {
        const val = obj["Bool"];
        return new Bool([val["_0"]]);
    }
    if ("U8" in obj) {
        const val = obj["U8"];
        return new U8([val["_0"]]);
    }
    if ("U8Array" in obj) {
        const val = obj["U8Array"];
        return new U8Array([val["_0"]]);
    }
    if ("U16" in obj) {
        const val = obj["U16"];
        return new U16([val["_0"]]);
    }
    if ("U64" in obj) {
        const val = obj["U64"];
        return new U64([val["_0"]]);
    }
    if ("U128" in obj) {
        const val = obj["U128"];
        return new U128([val["_0"]]);
    }
    if ("Pubkey" in obj) {
        const val = obj["Pubkey"];
        return new Pubkey([val["_0"]]);
    }
    if ("ElevationGroup" in obj) {
        const val = obj["ElevationGroup"];
        return new ElevationGroup([types.ElevationGroup.fromDecoded(val["_0"])]);
    }
    if ("Name" in obj) {
        const val = obj["Name"];
        return new Name([val["_0"]]);
    }
    throw new Error("Invalid enum object");
}
function fromJSON(obj) {
    switch (obj.kind) {
        case "Bool": {
            return new Bool([obj.value[0]]);
        }
        case "U8": {
            return new U8([obj.value[0]]);
        }
        case "U8Array": {
            return new U8Array([obj.value[0]]);
        }
        case "U16": {
            return new U16([obj.value[0]]);
        }
        case "U64": {
            return new U64([new bn_js_1.default(obj.value[0])]);
        }
        case "U128": {
            return new U128([new bn_js_1.default(obj.value[0])]);
        }
        case "Pubkey": {
            return new Pubkey([(0, kit_1.address)(obj.value[0])]);
        }
        case "ElevationGroup": {
            return new ElevationGroup([types.ElevationGroup.fromJSON(obj.value[0])]);
        }
        case "Name": {
            return new Name([obj.value[0]]);
        }
    }
}
function layout(property) {
    const ret = borsh.rustEnum([
        borsh.struct([borsh.bool("_0")], "Bool"),
        borsh.struct([borsh.u8("_0")], "U8"),
        borsh.struct([borsh.array(borsh.u8(), 8, "_0")], "U8Array"),
        borsh.struct([borsh.u16("_0")], "U16"),
        borsh.struct([borsh.u64("_0")], "U64"),
        borsh.struct([borsh.u128("_0")], "U128"),
        borsh.struct([(0, utils_1.borshAddress)("_0")], "Pubkey"),
        borsh.struct([types.ElevationGroup.layout("_0")], "ElevationGroup"),
        borsh.struct([borsh.array(borsh.u8(), 32, "_0")], "Name"),
    ]);
    if (property !== undefined) {
        return ret.replicate(property);
    }
    return ret;
}
//# sourceMappingURL=UpdateLendingMarketConfigValue.js.map