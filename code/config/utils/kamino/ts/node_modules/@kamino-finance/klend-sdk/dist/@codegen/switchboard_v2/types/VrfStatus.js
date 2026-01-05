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
exports.StatusVerifyFailure = exports.StatusCallbackSuccess = exports.StatusVerified = exports.StatusVerifying = exports.StatusRequesting = exports.StatusNone = void 0;
exports.fromDecoded = fromDecoded;
exports.fromJSON = fromJSON;
exports.layout = layout;
const borsh = __importStar(require("@coral-xyz/borsh"));
class StatusNone {
    static discriminator = 0;
    static kind = "StatusNone";
    discriminator = 0;
    kind = "StatusNone";
    toJSON() {
        return {
            kind: "StatusNone",
        };
    }
    toEncodable() {
        return {
            StatusNone: {},
        };
    }
}
exports.StatusNone = StatusNone;
class StatusRequesting {
    static discriminator = 1;
    static kind = "StatusRequesting";
    discriminator = 1;
    kind = "StatusRequesting";
    toJSON() {
        return {
            kind: "StatusRequesting",
        };
    }
    toEncodable() {
        return {
            StatusRequesting: {},
        };
    }
}
exports.StatusRequesting = StatusRequesting;
class StatusVerifying {
    static discriminator = 2;
    static kind = "StatusVerifying";
    discriminator = 2;
    kind = "StatusVerifying";
    toJSON() {
        return {
            kind: "StatusVerifying",
        };
    }
    toEncodable() {
        return {
            StatusVerifying: {},
        };
    }
}
exports.StatusVerifying = StatusVerifying;
class StatusVerified {
    static discriminator = 3;
    static kind = "StatusVerified";
    discriminator = 3;
    kind = "StatusVerified";
    toJSON() {
        return {
            kind: "StatusVerified",
        };
    }
    toEncodable() {
        return {
            StatusVerified: {},
        };
    }
}
exports.StatusVerified = StatusVerified;
class StatusCallbackSuccess {
    static discriminator = 4;
    static kind = "StatusCallbackSuccess";
    discriminator = 4;
    kind = "StatusCallbackSuccess";
    toJSON() {
        return {
            kind: "StatusCallbackSuccess",
        };
    }
    toEncodable() {
        return {
            StatusCallbackSuccess: {},
        };
    }
}
exports.StatusCallbackSuccess = StatusCallbackSuccess;
class StatusVerifyFailure {
    static discriminator = 5;
    static kind = "StatusVerifyFailure";
    discriminator = 5;
    kind = "StatusVerifyFailure";
    toJSON() {
        return {
            kind: "StatusVerifyFailure",
        };
    }
    toEncodable() {
        return {
            StatusVerifyFailure: {},
        };
    }
}
exports.StatusVerifyFailure = StatusVerifyFailure;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function fromDecoded(obj) {
    if (typeof obj !== "object") {
        throw new Error("Invalid enum object");
    }
    if ("StatusNone" in obj) {
        return new StatusNone();
    }
    if ("StatusRequesting" in obj) {
        return new StatusRequesting();
    }
    if ("StatusVerifying" in obj) {
        return new StatusVerifying();
    }
    if ("StatusVerified" in obj) {
        return new StatusVerified();
    }
    if ("StatusCallbackSuccess" in obj) {
        return new StatusCallbackSuccess();
    }
    if ("StatusVerifyFailure" in obj) {
        return new StatusVerifyFailure();
    }
    throw new Error("Invalid enum object");
}
function fromJSON(obj) {
    switch (obj.kind) {
        case "StatusNone": {
            return new StatusNone();
        }
        case "StatusRequesting": {
            return new StatusRequesting();
        }
        case "StatusVerifying": {
            return new StatusVerifying();
        }
        case "StatusVerified": {
            return new StatusVerified();
        }
        case "StatusCallbackSuccess": {
            return new StatusCallbackSuccess();
        }
        case "StatusVerifyFailure": {
            return new StatusVerifyFailure();
        }
    }
}
function layout(property) {
    const ret = borsh.rustEnum([
        borsh.struct([], "StatusNone"),
        borsh.struct([], "StatusRequesting"),
        borsh.struct([], "StatusVerifying"),
        borsh.struct([], "StatusVerified"),
        borsh.struct([], "StatusCallbackSuccess"),
        borsh.struct([], "StatusVerifyFailure"),
    ]);
    if (property !== undefined) {
        return ret.replicate(property);
    }
    return ret;
}
//# sourceMappingURL=VrfStatus.js.map