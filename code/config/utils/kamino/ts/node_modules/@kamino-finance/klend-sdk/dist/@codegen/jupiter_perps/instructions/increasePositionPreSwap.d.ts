import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface IncreasePositionPreSwapArgs {
    params: types.IncreasePositionPreSwapParamsFields;
}
export interface IncreasePositionPreSwapAccounts {
    keeper: TransactionSigner;
    keeperAta: Address;
    positionRequest: Address;
    positionRequestAta: Address;
    position: Address;
    collateralCustody: Address;
    collateralCustodyTokenAccount: Address;
    instruction: Address;
    tokenProgram: Address;
    eventAuthority: Address;
    program: Address;
}
export declare const layout: import("buffer-layout").Layout<IncreasePositionPreSwapArgs>;
export declare function increasePositionPreSwap(args: IncreasePositionPreSwapArgs, accounts: IncreasePositionPreSwapAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=increasePositionPreSwap.d.ts.map