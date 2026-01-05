import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DecreasePositionPostSwapArgs {
    params: types.DecreasePositionPostSwapParamsFields;
}
export interface DecreasePositionPostSwapAccounts {
    keeper: TransactionSigner;
    positionRequest: Address;
    positionRequestAta: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<DecreasePositionPostSwapArgs>;
export declare function decreasePositionPostSwap(args: DecreasePositionPostSwapArgs, accounts: DecreasePositionPostSwapAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=decreasePositionPostSwap.d.ts.map