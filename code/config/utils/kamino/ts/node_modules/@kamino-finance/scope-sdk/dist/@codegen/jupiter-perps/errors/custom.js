"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InvalidPriceCalcMode = exports.MissingPriceSlippage = exports.MissingTriggerPrice = exports.TriggerPriceSlippage = exports.InvalidTriggerPrice = exports.InvalidRequestType = exports.ExceedExecutionPeriod = exports.InvalidKeeper = exports.CPINotAllowed = exports.SwapAmountMismatch = exports.KeeperATAMissing = exports.AddressMismatch = exports.ProgramMismatch = exports.JupiterProgramMismatch = exports.InstructionNotAllowed = exports.UnsupportedToken = exports.PersonalPoolAmountLimit = exports.PoolAmountLimit = exports.CustodyAmountLimit = exports.MaxLeverage = exports.MaxPriceSlippage = exports.InsufficientAmountReturned = exports.InsufficientTokenAmount = exports.InvalidMint = exports.InvalidPositionRequestInputAta = exports.InvalidPositionRequest = exports.InvalidArgument = exports.InvalidCustodyBalance = exports.InvalidCustodyConfig = exports.InvalidInstruction = exports.InvalidPoolConfig = exports.InvalidPerpetualsConfig = exports.InvalidPositionState = exports.CollateralSlippage = exports.InvalidCollateralAmount = exports.InvalidCollateralAccount = exports.InvalidEnvironment = exports.InvalidOraclePrice = exports.StaleOraclePrice = exports.InvalidOracleAccount = exports.UnsupportedOracle = exports.MathOverflow = void 0;
exports.fromCode = fromCode;
class MathOverflow extends Error {
    logs;
    static code = 6000;
    code = 6000;
    name = "MathOverflow";
    msg = "Overflow in arithmetic operation";
    constructor(logs) {
        super("6000: Overflow in arithmetic operation");
        this.logs = logs;
    }
}
exports.MathOverflow = MathOverflow;
class UnsupportedOracle extends Error {
    logs;
    static code = 6001;
    code = 6001;
    name = "UnsupportedOracle";
    msg = "Unsupported price oracle";
    constructor(logs) {
        super("6001: Unsupported price oracle");
        this.logs = logs;
    }
}
exports.UnsupportedOracle = UnsupportedOracle;
class InvalidOracleAccount extends Error {
    logs;
    static code = 6002;
    code = 6002;
    name = "InvalidOracleAccount";
    msg = "Invalid oracle account";
    constructor(logs) {
        super("6002: Invalid oracle account");
        this.logs = logs;
    }
}
exports.InvalidOracleAccount = InvalidOracleAccount;
class StaleOraclePrice extends Error {
    logs;
    static code = 6003;
    code = 6003;
    name = "StaleOraclePrice";
    msg = "Stale oracle price";
    constructor(logs) {
        super("6003: Stale oracle price");
        this.logs = logs;
    }
}
exports.StaleOraclePrice = StaleOraclePrice;
class InvalidOraclePrice extends Error {
    logs;
    static code = 6004;
    code = 6004;
    name = "InvalidOraclePrice";
    msg = "Invalid oracle price";
    constructor(logs) {
        super("6004: Invalid oracle price");
        this.logs = logs;
    }
}
exports.InvalidOraclePrice = InvalidOraclePrice;
class InvalidEnvironment extends Error {
    logs;
    static code = 6005;
    code = 6005;
    name = "InvalidEnvironment";
    msg = "Instruction is not allowed in production";
    constructor(logs) {
        super("6005: Instruction is not allowed in production");
        this.logs = logs;
    }
}
exports.InvalidEnvironment = InvalidEnvironment;
class InvalidCollateralAccount extends Error {
    logs;
    static code = 6006;
    code = 6006;
    name = "InvalidCollateralAccount";
    msg = "Invalid collateral account";
    constructor(logs) {
        super("6006: Invalid collateral account");
        this.logs = logs;
    }
}
exports.InvalidCollateralAccount = InvalidCollateralAccount;
class InvalidCollateralAmount extends Error {
    logs;
    static code = 6007;
    code = 6007;
    name = "InvalidCollateralAmount";
    msg = "Invalid collateral amount";
    constructor(logs) {
        super("6007: Invalid collateral amount");
        this.logs = logs;
    }
}
exports.InvalidCollateralAmount = InvalidCollateralAmount;
class CollateralSlippage extends Error {
    logs;
    static code = 6008;
    code = 6008;
    name = "CollateralSlippage";
    msg = "Collateral slippage";
    constructor(logs) {
        super("6008: Collateral slippage");
        this.logs = logs;
    }
}
exports.CollateralSlippage = CollateralSlippage;
class InvalidPositionState extends Error {
    logs;
    static code = 6009;
    code = 6009;
    name = "InvalidPositionState";
    msg = "Invalid position state";
    constructor(logs) {
        super("6009: Invalid position state");
        this.logs = logs;
    }
}
exports.InvalidPositionState = InvalidPositionState;
class InvalidPerpetualsConfig extends Error {
    logs;
    static code = 6010;
    code = 6010;
    name = "InvalidPerpetualsConfig";
    msg = "Invalid perpetuals config";
    constructor(logs) {
        super("6010: Invalid perpetuals config");
        this.logs = logs;
    }
}
exports.InvalidPerpetualsConfig = InvalidPerpetualsConfig;
class InvalidPoolConfig extends Error {
    logs;
    static code = 6011;
    code = 6011;
    name = "InvalidPoolConfig";
    msg = "Invalid pool config";
    constructor(logs) {
        super("6011: Invalid pool config");
        this.logs = logs;
    }
}
exports.InvalidPoolConfig = InvalidPoolConfig;
class InvalidInstruction extends Error {
    logs;
    static code = 6012;
    code = 6012;
    name = "InvalidInstruction";
    msg = "Invalid instruction";
    constructor(logs) {
        super("6012: Invalid instruction");
        this.logs = logs;
    }
}
exports.InvalidInstruction = InvalidInstruction;
class InvalidCustodyConfig extends Error {
    logs;
    static code = 6013;
    code = 6013;
    name = "InvalidCustodyConfig";
    msg = "Invalid custody config";
    constructor(logs) {
        super("6013: Invalid custody config");
        this.logs = logs;
    }
}
exports.InvalidCustodyConfig = InvalidCustodyConfig;
class InvalidCustodyBalance extends Error {
    logs;
    static code = 6014;
    code = 6014;
    name = "InvalidCustodyBalance";
    msg = "Invalid custody balance";
    constructor(logs) {
        super("6014: Invalid custody balance");
        this.logs = logs;
    }
}
exports.InvalidCustodyBalance = InvalidCustodyBalance;
class InvalidArgument extends Error {
    logs;
    static code = 6015;
    code = 6015;
    name = "InvalidArgument";
    msg = "Invalid argument";
    constructor(logs) {
        super("6015: Invalid argument");
        this.logs = logs;
    }
}
exports.InvalidArgument = InvalidArgument;
class InvalidPositionRequest extends Error {
    logs;
    static code = 6016;
    code = 6016;
    name = "InvalidPositionRequest";
    msg = "Invalid position request";
    constructor(logs) {
        super("6016: Invalid position request");
        this.logs = logs;
    }
}
exports.InvalidPositionRequest = InvalidPositionRequest;
class InvalidPositionRequestInputAta extends Error {
    logs;
    static code = 6017;
    code = 6017;
    name = "InvalidPositionRequestInputAta";
    msg = "Invalid position request input ata";
    constructor(logs) {
        super("6017: Invalid position request input ata");
        this.logs = logs;
    }
}
exports.InvalidPositionRequestInputAta = InvalidPositionRequestInputAta;
class InvalidMint extends Error {
    logs;
    static code = 6018;
    code = 6018;
    name = "InvalidMint";
    msg = "Invalid mint";
    constructor(logs) {
        super("6018: Invalid mint");
        this.logs = logs;
    }
}
exports.InvalidMint = InvalidMint;
class InsufficientTokenAmount extends Error {
    logs;
    static code = 6019;
    code = 6019;
    name = "InsufficientTokenAmount";
    msg = "Insufficient token amount";
    constructor(logs) {
        super("6019: Insufficient token amount");
        this.logs = logs;
    }
}
exports.InsufficientTokenAmount = InsufficientTokenAmount;
class InsufficientAmountReturned extends Error {
    logs;
    static code = 6020;
    code = 6020;
    name = "InsufficientAmountReturned";
    msg = "Insufficient token amount returned";
    constructor(logs) {
        super("6020: Insufficient token amount returned");
        this.logs = logs;
    }
}
exports.InsufficientAmountReturned = InsufficientAmountReturned;
class MaxPriceSlippage extends Error {
    logs;
    static code = 6021;
    code = 6021;
    name = "MaxPriceSlippage";
    msg = "Price slippage limit exceeded";
    constructor(logs) {
        super("6021: Price slippage limit exceeded");
        this.logs = logs;
    }
}
exports.MaxPriceSlippage = MaxPriceSlippage;
class MaxLeverage extends Error {
    logs;
    static code = 6022;
    code = 6022;
    name = "MaxLeverage";
    msg = "Position leverage limit exceeded";
    constructor(logs) {
        super("6022: Position leverage limit exceeded");
        this.logs = logs;
    }
}
exports.MaxLeverage = MaxLeverage;
class CustodyAmountLimit extends Error {
    logs;
    static code = 6023;
    code = 6023;
    name = "CustodyAmountLimit";
    msg = "Custody amount limit exceeded";
    constructor(logs) {
        super("6023: Custody amount limit exceeded");
        this.logs = logs;
    }
}
exports.CustodyAmountLimit = CustodyAmountLimit;
class PoolAmountLimit extends Error {
    logs;
    static code = 6024;
    code = 6024;
    name = "PoolAmountLimit";
    msg = "Pool amount limit exceeded";
    constructor(logs) {
        super("6024: Pool amount limit exceeded");
        this.logs = logs;
    }
}
exports.PoolAmountLimit = PoolAmountLimit;
class PersonalPoolAmountLimit extends Error {
    logs;
    static code = 6025;
    code = 6025;
    name = "PersonalPoolAmountLimit";
    msg = "Personal pool amount limit exceeded";
    constructor(logs) {
        super("6025: Personal pool amount limit exceeded");
        this.logs = logs;
    }
}
exports.PersonalPoolAmountLimit = PersonalPoolAmountLimit;
class UnsupportedToken extends Error {
    logs;
    static code = 6026;
    code = 6026;
    name = "UnsupportedToken";
    msg = "Token is not supported";
    constructor(logs) {
        super("6026: Token is not supported");
        this.logs = logs;
    }
}
exports.UnsupportedToken = UnsupportedToken;
class InstructionNotAllowed extends Error {
    logs;
    static code = 6027;
    code = 6027;
    name = "InstructionNotAllowed";
    msg = "Instruction is not allowed at this time";
    constructor(logs) {
        super("6027: Instruction is not allowed at this time");
        this.logs = logs;
    }
}
exports.InstructionNotAllowed = InstructionNotAllowed;
class JupiterProgramMismatch extends Error {
    logs;
    static code = 6028;
    code = 6028;
    name = "JupiterProgramMismatch";
    msg = "Jupiter Program ID mismatch";
    constructor(logs) {
        super("6028: Jupiter Program ID mismatch");
        this.logs = logs;
    }
}
exports.JupiterProgramMismatch = JupiterProgramMismatch;
class ProgramMismatch extends Error {
    logs;
    static code = 6029;
    code = 6029;
    name = "ProgramMismatch";
    msg = "Program ID mismatch";
    constructor(logs) {
        super("6029: Program ID mismatch");
        this.logs = logs;
    }
}
exports.ProgramMismatch = ProgramMismatch;
class AddressMismatch extends Error {
    logs;
    static code = 6030;
    code = 6030;
    name = "AddressMismatch";
    msg = "Address mismatch";
    constructor(logs) {
        super("6030: Address mismatch");
        this.logs = logs;
    }
}
exports.AddressMismatch = AddressMismatch;
class KeeperATAMissing extends Error {
    logs;
    static code = 6031;
    code = 6031;
    name = "KeeperATAMissing";
    msg = "Missing keeper ATA";
    constructor(logs) {
        super("6031: Missing keeper ATA");
        this.logs = logs;
    }
}
exports.KeeperATAMissing = KeeperATAMissing;
class SwapAmountMismatch extends Error {
    logs;
    static code = 6032;
    code = 6032;
    name = "SwapAmountMismatch";
    msg = "Swap amount mismatch";
    constructor(logs) {
        super("6032: Swap amount mismatch");
        this.logs = logs;
    }
}
exports.SwapAmountMismatch = SwapAmountMismatch;
class CPINotAllowed extends Error {
    logs;
    static code = 6033;
    code = 6033;
    name = "CPINotAllowed";
    msg = "CPI not allowed";
    constructor(logs) {
        super("6033: CPI not allowed");
        this.logs = logs;
    }
}
exports.CPINotAllowed = CPINotAllowed;
class InvalidKeeper extends Error {
    logs;
    static code = 6034;
    code = 6034;
    name = "InvalidKeeper";
    msg = "Invalid Keeper";
    constructor(logs) {
        super("6034: Invalid Keeper");
        this.logs = logs;
    }
}
exports.InvalidKeeper = InvalidKeeper;
class ExceedExecutionPeriod extends Error {
    logs;
    static code = 6035;
    code = 6035;
    name = "ExceedExecutionPeriod";
    msg = "Exceed execution period";
    constructor(logs) {
        super("6035: Exceed execution period");
        this.logs = logs;
    }
}
exports.ExceedExecutionPeriod = ExceedExecutionPeriod;
class InvalidRequestType extends Error {
    logs;
    static code = 6036;
    code = 6036;
    name = "InvalidRequestType";
    msg = "Invalid Request Type";
    constructor(logs) {
        super("6036: Invalid Request Type");
        this.logs = logs;
    }
}
exports.InvalidRequestType = InvalidRequestType;
class InvalidTriggerPrice extends Error {
    logs;
    static code = 6037;
    code = 6037;
    name = "InvalidTriggerPrice";
    msg = "Invalid Trigger Price";
    constructor(logs) {
        super("6037: Invalid Trigger Price");
        this.logs = logs;
    }
}
exports.InvalidTriggerPrice = InvalidTriggerPrice;
class TriggerPriceSlippage extends Error {
    logs;
    static code = 6038;
    code = 6038;
    name = "TriggerPriceSlippage";
    msg = "Trigger Price Slippage";
    constructor(logs) {
        super("6038: Trigger Price Slippage");
        this.logs = logs;
    }
}
exports.TriggerPriceSlippage = TriggerPriceSlippage;
class MissingTriggerPrice extends Error {
    logs;
    static code = 6039;
    code = 6039;
    name = "MissingTriggerPrice";
    msg = "Missing Trigger Price";
    constructor(logs) {
        super("6039: Missing Trigger Price");
        this.logs = logs;
    }
}
exports.MissingTriggerPrice = MissingTriggerPrice;
class MissingPriceSlippage extends Error {
    logs;
    static code = 6040;
    code = 6040;
    name = "MissingPriceSlippage";
    msg = "Missing Price Slippage";
    constructor(logs) {
        super("6040: Missing Price Slippage");
        this.logs = logs;
    }
}
exports.MissingPriceSlippage = MissingPriceSlippage;
class InvalidPriceCalcMode extends Error {
    logs;
    static code = 6041;
    code = 6041;
    name = "InvalidPriceCalcMode";
    msg = "Invalid price calc mode";
    constructor(logs) {
        super("6041: Invalid price calc mode");
        this.logs = logs;
    }
}
exports.InvalidPriceCalcMode = InvalidPriceCalcMode;
function fromCode(code, logs) {
    switch (code) {
        case 6000:
            return new MathOverflow(logs);
        case 6001:
            return new UnsupportedOracle(logs);
        case 6002:
            return new InvalidOracleAccount(logs);
        case 6003:
            return new StaleOraclePrice(logs);
        case 6004:
            return new InvalidOraclePrice(logs);
        case 6005:
            return new InvalidEnvironment(logs);
        case 6006:
            return new InvalidCollateralAccount(logs);
        case 6007:
            return new InvalidCollateralAmount(logs);
        case 6008:
            return new CollateralSlippage(logs);
        case 6009:
            return new InvalidPositionState(logs);
        case 6010:
            return new InvalidPerpetualsConfig(logs);
        case 6011:
            return new InvalidPoolConfig(logs);
        case 6012:
            return new InvalidInstruction(logs);
        case 6013:
            return new InvalidCustodyConfig(logs);
        case 6014:
            return new InvalidCustodyBalance(logs);
        case 6015:
            return new InvalidArgument(logs);
        case 6016:
            return new InvalidPositionRequest(logs);
        case 6017:
            return new InvalidPositionRequestInputAta(logs);
        case 6018:
            return new InvalidMint(logs);
        case 6019:
            return new InsufficientTokenAmount(logs);
        case 6020:
            return new InsufficientAmountReturned(logs);
        case 6021:
            return new MaxPriceSlippage(logs);
        case 6022:
            return new MaxLeverage(logs);
        case 6023:
            return new CustodyAmountLimit(logs);
        case 6024:
            return new PoolAmountLimit(logs);
        case 6025:
            return new PersonalPoolAmountLimit(logs);
        case 6026:
            return new UnsupportedToken(logs);
        case 6027:
            return new InstructionNotAllowed(logs);
        case 6028:
            return new JupiterProgramMismatch(logs);
        case 6029:
            return new ProgramMismatch(logs);
        case 6030:
            return new AddressMismatch(logs);
        case 6031:
            return new KeeperATAMissing(logs);
        case 6032:
            return new SwapAmountMismatch(logs);
        case 6033:
            return new CPINotAllowed(logs);
        case 6034:
            return new InvalidKeeper(logs);
        case 6035:
            return new ExceedExecutionPeriod(logs);
        case 6036:
            return new InvalidRequestType(logs);
        case 6037:
            return new InvalidTriggerPrice(logs);
        case 6038:
            return new TriggerPriceSlippage(logs);
        case 6039:
            return new MissingTriggerPrice(logs);
        case 6040:
            return new MissingPriceSlippage(logs);
        case 6041:
            return new InvalidPriceCalcMode(logs);
    }
    return null;
}
//# sourceMappingURL=custom.js.map