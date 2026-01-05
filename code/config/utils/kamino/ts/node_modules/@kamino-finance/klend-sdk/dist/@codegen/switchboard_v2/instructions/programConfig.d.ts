import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface ProgramConfigArgs {
    params: types.ProgramConfigParamsFields;
}
export interface ProgramConfigAccounts {
    authority: TransactionSigner;
    programState: Address;
    daoMint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function programConfig(args: ProgramConfigArgs, accounts: ProgramConfigAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=programConfig.d.ts.map