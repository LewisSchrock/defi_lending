import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfCloseActionArgs {
    params: types.VrfCloseParamsFields;
}
export interface VrfCloseActionAccounts {
    authority: TransactionSigner;
    vrf: Address;
    permission: Address;
    oracleQueue: Address;
    queueAuthority: Address;
    programState: Address;
    escrow: Address;
    solDest: Address;
    escrowDest: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfCloseAction(args: VrfCloseActionArgs, accounts: VrfCloseActionAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfCloseAction.d.ts.map