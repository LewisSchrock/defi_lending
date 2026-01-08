"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LendingObligation = exports.LeverageObligation = exports.MultiplyObligation = exports.VanillaObligation = exports.ObligationTypeTag = void 0;
exports.getObligationPdaWithArgs = getObligationPdaWithArgs;
exports.getObligationType = getObligationType;
exports.getObligationTypeFromObligation = getObligationTypeFromObligation;
const kit_1 = require("@solana/kit");
const pubkey_1 = require("./pubkey");
const addressEncoder = (0, kit_1.getAddressEncoder)();
var ObligationTypeTag;
(function (ObligationTypeTag) {
    ObligationTypeTag[ObligationTypeTag["Vanilla"] = 0] = "Vanilla";
    ObligationTypeTag[ObligationTypeTag["Multiply"] = 1] = "Multiply";
    ObligationTypeTag[ObligationTypeTag["Lending"] = 2] = "Lending";
    ObligationTypeTag[ObligationTypeTag["Leverage"] = 3] = "Leverage";
})(ObligationTypeTag || (exports.ObligationTypeTag = ObligationTypeTag = {}));
class VanillaObligation {
    programId;
    id;
    static tag = 0;
    constructor(programId, id) {
        this.programId = programId;
        this.id = id ?? 0;
    }
    toArgs() {
        const initObligationArgs = {
            tag: VanillaObligation.tag,
            id: this.id,
            seed1: pubkey_1.DEFAULT_PUBLIC_KEY,
            seed2: pubkey_1.DEFAULT_PUBLIC_KEY,
        };
        return initObligationArgs;
    }
    toPda(market, user) {
        return getObligationPdaWithArgs(market, user, this.toArgs(), this.programId);
    }
}
exports.VanillaObligation = VanillaObligation;
class MultiplyObligation {
    collToken;
    debtToken;
    programId;
    id;
    static tag = 1;
    constructor(collToken, debtToken, programId, id) {
        this.collToken = collToken;
        this.debtToken = debtToken;
        this.programId = programId;
        this.id = id ?? 0;
    }
    toArgs() {
        const initObligationArgs = {
            tag: MultiplyObligation.tag,
            id: this.id,
            seed1: this.collToken,
            seed2: this.debtToken,
        };
        return initObligationArgs;
    }
    toPda(market, user) {
        return getObligationPdaWithArgs(market, user, this.toArgs(), this.programId);
    }
}
exports.MultiplyObligation = MultiplyObligation;
class LeverageObligation {
    collToken;
    debtToken;
    programId;
    id;
    static tag = 3;
    constructor(collToken, debtToken, programId, id) {
        this.collToken = collToken;
        this.debtToken = debtToken;
        this.programId = programId;
        this.id = id ?? 0;
    }
    toArgs() {
        const initObligationArgs = {
            tag: LeverageObligation.tag,
            id: this.id,
            seed1: this.collToken,
            seed2: this.debtToken,
        };
        return initObligationArgs;
    }
    toPda(market, user) {
        return getObligationPdaWithArgs(market, user, this.toArgs(), this.programId);
    }
}
exports.LeverageObligation = LeverageObligation;
class LendingObligation {
    token;
    programId;
    id;
    static tag = 2;
    constructor(token, programId, id) {
        this.token = token;
        this.programId = programId;
        this.id = id ?? 0;
    }
    toArgs() {
        const initObligationArgs = {
            tag: LendingObligation.tag,
            id: 0,
            seed1: this.token,
            seed2: this.token,
        };
        return initObligationArgs;
    }
    toPda(market, user) {
        return getObligationPdaWithArgs(market, user, this.toArgs(), this.programId);
    }
}
exports.LendingObligation = LendingObligation;
async function getObligationPdaWithArgs(market, user, args, programId) {
    const seeds = [
        Buffer.from([args.tag]),
        Buffer.from([args.id]),
        addressEncoder.encode(user),
        addressEncoder.encode(market),
        addressEncoder.encode(args.seed1),
        addressEncoder.encode(args.seed2),
    ];
    const [obligationAddress, _obligationAddressBump] = await (0, kit_1.getProgramDerivedAddress)({
        seeds,
        programAddress: programId,
    });
    return obligationAddress;
}
function getObligationType(kaminoMarket, obligationTag, mintAddress1 = (0, kit_1.none)(), mintAddress2 = (0, kit_1.none)()) {
    switch (obligationTag) {
        case VanillaObligation.tag: {
            return new VanillaObligation(kaminoMarket.programId);
        }
        case MultiplyObligation.tag: {
            if ((0, kit_1.isNone)(mintAddress1)) {
                throw new Error(`Multiply obligation PDA requires mint address 1`);
            }
            if ((0, kit_1.isNone)(mintAddress2)) {
                throw new Error(`Multiply obligation PDA requires mint address 2`);
            }
            return new MultiplyObligation(mintAddress1.value, mintAddress2.value, kaminoMarket.programId);
        }
        case LeverageObligation.tag: {
            if ((0, kit_1.isNone)(mintAddress1)) {
                throw new Error(`Leverage obligation PDA requires mint address 1`);
            }
            if ((0, kit_1.isNone)(mintAddress2)) {
                throw new Error(`Leverage obligation PDA requires mint address 2`);
            }
            return new LeverageObligation(mintAddress1.value, mintAddress2.value, kaminoMarket.programId);
        }
        case LendingObligation.tag: {
            if ((0, kit_1.isNone)(mintAddress1)) {
                throw new Error(`Lending obligation PDA requires mint address 1`);
            }
            return new LendingObligation(mintAddress1.value, kaminoMarket.programId);
        }
        default: {
            throw new Error('Invalid obligation type');
        }
    }
}
function getObligationTypeFromObligation(kaminoMarket, obligation) {
    switch (obligation.obligationTag) {
        case VanillaObligation.tag: {
            return new VanillaObligation(kaminoMarket.programId);
        }
        case MultiplyObligation.tag: {
            return new MultiplyObligation(obligation.getDeposits()[0].mintAddress, obligation.getBorrows()[0].mintAddress, kaminoMarket.programId);
        }
        case LeverageObligation.tag: {
            return new LeverageObligation(obligation.getDeposits()[0].mintAddress, obligation.getBorrows()[0].mintAddress, kaminoMarket.programId);
        }
        case LendingObligation.tag: {
            return new LendingObligation(obligation.getDeposits()[0].mintAddress, kaminoMarket.programId);
        }
        default: {
            throw new Error('Invalid obligation type');
        }
    }
}
//# sourceMappingURL=ObligationType.js.map