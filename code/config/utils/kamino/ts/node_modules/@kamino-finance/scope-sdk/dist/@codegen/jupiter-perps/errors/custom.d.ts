export type CustomError = MathOverflow | UnsupportedOracle | InvalidOracleAccount | StaleOraclePrice | InvalidOraclePrice | InvalidEnvironment | InvalidCollateralAccount | InvalidCollateralAmount | CollateralSlippage | InvalidPositionState | InvalidPerpetualsConfig | InvalidPoolConfig | InvalidInstruction | InvalidCustodyConfig | InvalidCustodyBalance | InvalidArgument | InvalidPositionRequest | InvalidPositionRequestInputAta | InvalidMint | InsufficientTokenAmount | InsufficientAmountReturned | MaxPriceSlippage | MaxLeverage | CustodyAmountLimit | PoolAmountLimit | PersonalPoolAmountLimit | UnsupportedToken | InstructionNotAllowed | JupiterProgramMismatch | ProgramMismatch | AddressMismatch | KeeperATAMissing | SwapAmountMismatch | CPINotAllowed | InvalidKeeper | ExceedExecutionPeriod | InvalidRequestType | InvalidTriggerPrice | TriggerPriceSlippage | MissingTriggerPrice | MissingPriceSlippage | InvalidPriceCalcMode;
export declare class MathOverflow extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6000;
    readonly code = 6000;
    readonly name = "MathOverflow";
    readonly msg = "Overflow in arithmetic operation";
    constructor(logs?: string[] | undefined);
}
export declare class UnsupportedOracle extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6001;
    readonly code = 6001;
    readonly name = "UnsupportedOracle";
    readonly msg = "Unsupported price oracle";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidOracleAccount extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6002;
    readonly code = 6002;
    readonly name = "InvalidOracleAccount";
    readonly msg = "Invalid oracle account";
    constructor(logs?: string[] | undefined);
}
export declare class StaleOraclePrice extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6003;
    readonly code = 6003;
    readonly name = "StaleOraclePrice";
    readonly msg = "Stale oracle price";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidOraclePrice extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6004;
    readonly code = 6004;
    readonly name = "InvalidOraclePrice";
    readonly msg = "Invalid oracle price";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidEnvironment extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6005;
    readonly code = 6005;
    readonly name = "InvalidEnvironment";
    readonly msg = "Instruction is not allowed in production";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidCollateralAccount extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6006;
    readonly code = 6006;
    readonly name = "InvalidCollateralAccount";
    readonly msg = "Invalid collateral account";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidCollateralAmount extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6007;
    readonly code = 6007;
    readonly name = "InvalidCollateralAmount";
    readonly msg = "Invalid collateral amount";
    constructor(logs?: string[] | undefined);
}
export declare class CollateralSlippage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6008;
    readonly code = 6008;
    readonly name = "CollateralSlippage";
    readonly msg = "Collateral slippage";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPositionState extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6009;
    readonly code = 6009;
    readonly name = "InvalidPositionState";
    readonly msg = "Invalid position state";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPerpetualsConfig extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6010;
    readonly code = 6010;
    readonly name = "InvalidPerpetualsConfig";
    readonly msg = "Invalid perpetuals config";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPoolConfig extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6011;
    readonly code = 6011;
    readonly name = "InvalidPoolConfig";
    readonly msg = "Invalid pool config";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidInstruction extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6012;
    readonly code = 6012;
    readonly name = "InvalidInstruction";
    readonly msg = "Invalid instruction";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidCustodyConfig extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6013;
    readonly code = 6013;
    readonly name = "InvalidCustodyConfig";
    readonly msg = "Invalid custody config";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidCustodyBalance extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6014;
    readonly code = 6014;
    readonly name = "InvalidCustodyBalance";
    readonly msg = "Invalid custody balance";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidArgument extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6015;
    readonly code = 6015;
    readonly name = "InvalidArgument";
    readonly msg = "Invalid argument";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPositionRequest extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6016;
    readonly code = 6016;
    readonly name = "InvalidPositionRequest";
    readonly msg = "Invalid position request";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPositionRequestInputAta extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6017;
    readonly code = 6017;
    readonly name = "InvalidPositionRequestInputAta";
    readonly msg = "Invalid position request input ata";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidMint extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6018;
    readonly code = 6018;
    readonly name = "InvalidMint";
    readonly msg = "Invalid mint";
    constructor(logs?: string[] | undefined);
}
export declare class InsufficientTokenAmount extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6019;
    readonly code = 6019;
    readonly name = "InsufficientTokenAmount";
    readonly msg = "Insufficient token amount";
    constructor(logs?: string[] | undefined);
}
export declare class InsufficientAmountReturned extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6020;
    readonly code = 6020;
    readonly name = "InsufficientAmountReturned";
    readonly msg = "Insufficient token amount returned";
    constructor(logs?: string[] | undefined);
}
export declare class MaxPriceSlippage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6021;
    readonly code = 6021;
    readonly name = "MaxPriceSlippage";
    readonly msg = "Price slippage limit exceeded";
    constructor(logs?: string[] | undefined);
}
export declare class MaxLeverage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6022;
    readonly code = 6022;
    readonly name = "MaxLeverage";
    readonly msg = "Position leverage limit exceeded";
    constructor(logs?: string[] | undefined);
}
export declare class CustodyAmountLimit extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6023;
    readonly code = 6023;
    readonly name = "CustodyAmountLimit";
    readonly msg = "Custody amount limit exceeded";
    constructor(logs?: string[] | undefined);
}
export declare class PoolAmountLimit extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6024;
    readonly code = 6024;
    readonly name = "PoolAmountLimit";
    readonly msg = "Pool amount limit exceeded";
    constructor(logs?: string[] | undefined);
}
export declare class PersonalPoolAmountLimit extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6025;
    readonly code = 6025;
    readonly name = "PersonalPoolAmountLimit";
    readonly msg = "Personal pool amount limit exceeded";
    constructor(logs?: string[] | undefined);
}
export declare class UnsupportedToken extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6026;
    readonly code = 6026;
    readonly name = "UnsupportedToken";
    readonly msg = "Token is not supported";
    constructor(logs?: string[] | undefined);
}
export declare class InstructionNotAllowed extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6027;
    readonly code = 6027;
    readonly name = "InstructionNotAllowed";
    readonly msg = "Instruction is not allowed at this time";
    constructor(logs?: string[] | undefined);
}
export declare class JupiterProgramMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6028;
    readonly code = 6028;
    readonly name = "JupiterProgramMismatch";
    readonly msg = "Jupiter Program ID mismatch";
    constructor(logs?: string[] | undefined);
}
export declare class ProgramMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6029;
    readonly code = 6029;
    readonly name = "ProgramMismatch";
    readonly msg = "Program ID mismatch";
    constructor(logs?: string[] | undefined);
}
export declare class AddressMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6030;
    readonly code = 6030;
    readonly name = "AddressMismatch";
    readonly msg = "Address mismatch";
    constructor(logs?: string[] | undefined);
}
export declare class KeeperATAMissing extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6031;
    readonly code = 6031;
    readonly name = "KeeperATAMissing";
    readonly msg = "Missing keeper ATA";
    constructor(logs?: string[] | undefined);
}
export declare class SwapAmountMismatch extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6032;
    readonly code = 6032;
    readonly name = "SwapAmountMismatch";
    readonly msg = "Swap amount mismatch";
    constructor(logs?: string[] | undefined);
}
export declare class CPINotAllowed extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6033;
    readonly code = 6033;
    readonly name = "CPINotAllowed";
    readonly msg = "CPI not allowed";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidKeeper extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6034;
    readonly code = 6034;
    readonly name = "InvalidKeeper";
    readonly msg = "Invalid Keeper";
    constructor(logs?: string[] | undefined);
}
export declare class ExceedExecutionPeriod extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6035;
    readonly code = 6035;
    readonly name = "ExceedExecutionPeriod";
    readonly msg = "Exceed execution period";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidRequestType extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6036;
    readonly code = 6036;
    readonly name = "InvalidRequestType";
    readonly msg = "Invalid Request Type";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidTriggerPrice extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6037;
    readonly code = 6037;
    readonly name = "InvalidTriggerPrice";
    readonly msg = "Invalid Trigger Price";
    constructor(logs?: string[] | undefined);
}
export declare class TriggerPriceSlippage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6038;
    readonly code = 6038;
    readonly name = "TriggerPriceSlippage";
    readonly msg = "Trigger Price Slippage";
    constructor(logs?: string[] | undefined);
}
export declare class MissingTriggerPrice extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6039;
    readonly code = 6039;
    readonly name = "MissingTriggerPrice";
    readonly msg = "Missing Trigger Price";
    constructor(logs?: string[] | undefined);
}
export declare class MissingPriceSlippage extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6040;
    readonly code = 6040;
    readonly name = "MissingPriceSlippage";
    readonly msg = "Missing Price Slippage";
    constructor(logs?: string[] | undefined);
}
export declare class InvalidPriceCalcMode extends Error {
    readonly logs?: string[] | undefined;
    static readonly code = 6041;
    readonly code = 6041;
    readonly name = "InvalidPriceCalcMode";
    readonly msg = "Invalid price calc mode";
    constructor(logs?: string[] | undefined);
}
export declare function fromCode(code: number, logs?: string[]): CustomError | null;
//# sourceMappingURL=custom.d.ts.map