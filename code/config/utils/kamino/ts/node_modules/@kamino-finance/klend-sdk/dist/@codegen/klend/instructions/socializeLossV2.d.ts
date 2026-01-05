import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SocializeLossV2Args {
    liquidityAmount: BN;
}
export interface SocializeLossV2Accounts {
    socializeLossAccounts: {
        riskCouncil: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        reserve: Address;
        instructionSysvarAccount: Address;
    };
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    lendingMarketAuthority: Address;
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<SocializeLossV2Args>;
export declare function socializeLossV2(args: SocializeLossV2Args, accounts: SocializeLossV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=socializeLossV2.d.ts.map