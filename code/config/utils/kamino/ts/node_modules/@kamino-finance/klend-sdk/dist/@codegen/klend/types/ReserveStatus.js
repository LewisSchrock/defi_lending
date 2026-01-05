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
exports.Hidden = exports.Obsolete = exports.Active = void 0;
exports.fromDecoded = fromDecoded;
exports.fromJSON = fromJSON;
exports.layout = layout;
const borsh = __importStar(require("@coral-xyz/borsh"));
class Active {
    static discriminator = 0;
    static kind = "Active";
    discriminator = 0;
    kind = "Active";
    toJSON() {
        return {
            kind: "Active",
        };
    }
    toEncodable() {
        return {
            Active: {},
        };
    }
}
exports.Active = Active;
class Obsolete {
    static discriminator = 1;
    static kind = "Obsolete";
    discriminator = 1;
    kind = "Obsolete";
    toJSON() {
        return {
            kind: "Obsolete",
        };
    }
    toEncodable() {
        return {
            Obsolete: {},
        };
    }
}
exports.Obsolete = Obsolete;
class Hidden {
    static discriminator = 2;
    static kind = "Hidden";
    discriminator = 2;
    kind = "Hidden";
    toJSON() {
        return {
            kind: "Hidden",
        };
    }
    toEncodable() {
        return {
            Hidden: {},
        };
    }
}
exports.Hidden = Hidden;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function fromDecoded(obj) {
    if (typeof obj !== "object") {
        throw new Error("Invalid enum object");
    }
    if ("Active" in obj) {
        return new Active();
    }
    if ("Obsolete" in obj) {
        return new Obsolete();
    }
    if ("Hidden" in obj) {
        return new Hidden();
    }
    throw new Error("Invalid enum object");
}
function fromJSON(obj) {
    switch (obj.kind) {
        case "Active": {
            return new Active();
        }
        case "Obsolete": {
            return new Obsolete();
        }
        case "Hidden": {
            return new Hidden();
        }
    }
}
function layout(property) {
    const ret = borsh.rustEnum([
        borsh.struct([], "Active"),
        borsh.struct([], "Obsolete"),
        borsh.struct([], "Hidden"),
    ]);
    if (property !== undefined) {
        return ret.replicate(property);
    }
    return ret;
}
//# sourceMappingURL=ReserveStatus.js.map