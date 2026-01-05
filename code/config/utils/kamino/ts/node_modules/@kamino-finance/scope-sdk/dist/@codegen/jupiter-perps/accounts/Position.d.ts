import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface PositionFields {
    owner: Address;
    pool: Address;
    custody: Address;
    collateralCustody: Address;
    openTime: BN;
    updateTime: BN;
    side: types.SideKind;
    price: BN;
    sizeUsd: BN;
    collateralUsd: BN;
    realisedPnlUsd: BN;
    cumulativeInterestSnapshot: BN;
    lockedAmount: BN;
    bump: number;
}
export interface PositionJSON {
    owner: string;
    pool: string;
    custody: string;
    collateralCustody: string;
    openTime: string;
    updateTime: string;
    side: types.SideJSON;
    price: string;
    sizeUsd: string;
    collateralUsd: string;
    realisedPnlUsd: string;
    cumulativeInterestSnapshot: string;
    lockedAmount: string;
    bump: number;
}
export declare class Position {
    readonly owner: Address;
    readonly pool: Address;
    readonly custody: Address;
    readonly collateralCustody: Address;
    readonly openTime: BN;
    readonly updateTime: BN;
    readonly side: types.SideKind;
    readonly price: BN;
    readonly sizeUsd: BN;
    readonly collateralUsd: BN;
    readonly realisedPnlUsd: BN;
    readonly cumulativeInterestSnapshot: BN;
    readonly lockedAmount: BN;
    readonly bump: number;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Position>;
    constructor(fields: PositionFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Position | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Position | null>>;
    static decode(data: Buffer): Position;
    toJSON(): PositionJSON;
    static fromJSON(obj: PositionJSON): Position;
}
//# sourceMappingURL=Position.d.ts.map