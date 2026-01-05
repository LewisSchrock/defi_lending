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
exports.Decrease = exports.Increase = exports.None = void 0;
exports.fromDecoded = fromDecoded;
exports.fromJSON = fromJSON;
exports.layout = layout;
const borsh = __importStar(require("@coral-xyz/borsh"));
class None {
    static discriminator = 0;
    static kind = "None";
    discriminator = 0;
    kind = "None";
    toJSON() {
        return {
            kind: "None",
        };
    }
    toEncodable() {
        return {
            None: {},
        };
    }
}
exports.None = None;
class Increase {
    static discriminator = 1;
    static kind = "Increase";
    discriminator = 1;
    kind = "Increase";
    toJSON() {
        return {
            kind: "Increase",
        };
    }
    toEncodable() {
        return {
            Increase: {},
        };
    }
}
exports.Increase = Increase;
class Decrease {
    static discriminator = 2;
    static kind = "Decrease";
    discriminator = 2;
    kind = "Decrease";
    toJSON() {
        return {
            kind: "Decrease",
        };
    }
    toEncodable() {
        return {
            Decrease: {},
        };
    }
}
exports.Decrease = Decrease;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function fromDecoded(obj) {
    if (typeof obj !== "object") {
        throw new Error("Invalid enum object");
    }
    if ("None" in obj) {
        return new None();
    }
    if ("Increase" in obj) {
        return new Increase();
    }
    if ("Decrease" in obj) {
        return new Decrease();
    }
    throw new Error("Invalid enum object");
}
function fromJSON(obj) {
    switch (obj.kind) {
        case "None": {
            return new None();
        }
        case "Increase": {
            return new Increase();
        }
        case "Decrease": {
            return new Decrease();
        }
    }
}
function layout(property) {
    const ret = borsh.rustEnum([
        borsh.struct([], "None"),
        borsh.struct([], "Increase"),
        borsh.struct([], "Decrease"),
    ]);
    if (property !== undefined) {
        return ret.replicate(property);
    }
    return ret;
}
//# sourceMappingURL=RequestChange.js.map