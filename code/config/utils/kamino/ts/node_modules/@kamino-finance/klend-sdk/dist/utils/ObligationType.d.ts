import { Address, Option } from '@solana/kit';
import { KaminoMarket, KaminoObligation } from '../classes';
export type ObligationType = VanillaObligation | MultiplyObligation | LendingObligation | LeverageObligation;
export declare enum ObligationTypeTag {
    Vanilla = 0,
    Multiply = 1,
    Lending = 2,
    Leverage = 3
}
export type InitObligationArgsModel = {
    tag: number;
    id: number;
    seed1: Address;
    seed2: Address;
};
export declare class VanillaObligation {
    readonly programId: Address;
    readonly id: number;
    static tag: number;
    constructor(programId: Address, id?: number);
    toArgs(): InitObligationArgsModel;
    toPda(market: Address, user: Address): Promise<Address>;
}
export declare class MultiplyObligation {
    readonly collToken: Address;
    readonly debtToken: Address;
    readonly programId: Address;
    readonly id: number;
    static tag: number;
    constructor(collToken: Address, debtToken: Address, programId: Address, id?: number);
    toArgs(): InitObligationArgsModel;
    toPda(market: Address, user: Address): Promise<Address>;
}
export declare class LeverageObligation {
    readonly collToken: Address;
    readonly debtToken: Address;
    readonly programId: Address;
    readonly id: number;
    static tag: number;
    constructor(collToken: Address, debtToken: Address, programId: Address, id?: number);
    toArgs(): InitObligationArgsModel;
    toPda(market: Address, user: Address): Promise<Address>;
}
export declare class LendingObligation {
    readonly token: Address;
    readonly programId: Address;
    readonly id: number;
    static tag: number;
    constructor(token: Address, programId: Address, id?: number);
    toArgs(): InitObligationArgsModel;
    toPda(market: Address, user: Address): Promise<Address>;
}
export declare function getObligationPdaWithArgs(market: Address, user: Address, args: InitObligationArgsModel, programId: Address): Promise<Address>;
export declare function getObligationType(kaminoMarket: KaminoMarket, obligationTag: ObligationTypeTag, mintAddress1?: Option<Address>, mintAddress2?: Option<Address>): ObligationType;
export declare function getObligationTypeFromObligation(kaminoMarket: KaminoMarket, obligation: KaminoObligation): ObligationType;
//# sourceMappingURL=ObligationType.d.ts.map