import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetWormholeAddressArgs {
    wormhole: Address;
}
export interface SetWormholeAddressAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare const layout: import("buffer-layout").Layout<SetWormholeAddressArgs>;
export declare function setWormholeAddress(args: SetWormholeAddressArgs, accounts: SetWormholeAddressAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setWormholeAddress.d.ts.map