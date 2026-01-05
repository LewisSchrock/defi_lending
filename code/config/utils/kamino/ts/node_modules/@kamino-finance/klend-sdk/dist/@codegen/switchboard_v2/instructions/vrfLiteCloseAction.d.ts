import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfLiteCloseActionArgs {
    params: types.VrfLiteCloseParamsFields;
}
export interface VrfLiteCloseActionAccounts {
    authority: TransactionSigner;
    vrfLite: Address;
    permission: Address;
    queue: Address;
    queueAuthority: Address;
    programState: Address;
    escrow: Address;
    solDest: Address;
    escrowDest: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfLiteCloseAction(args: VrfLiteCloseActionArgs, accounts: VrfLiteCloseActionAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfLiteCloseAction.d.ts.map