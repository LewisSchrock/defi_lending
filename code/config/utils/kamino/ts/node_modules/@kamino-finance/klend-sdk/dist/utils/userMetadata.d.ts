import { Address, Instruction, Rpc, GetProgramAccountsApi, GetProgramAccountsMemcmpFilter, GetProgramAccountsDatasizeFilter, TransactionSigner, Option } from '@solana/kit';
import { KaminoMarket, KaminoObligation } from '../classes';
import { UserMetadata } from '../lib';
export type KaminoUserMetadata = {
    address: Address;
    state: UserMetadata;
};
export declare const getUserLutAddressAndSetupIxs: (kaminoMarket: KaminoMarket, user: TransactionSigner, referrer?: Option<Address>, withExtendLut?: boolean, multiplyMints?: {
    coll: Address;
    debt: Address;
}[], leverageMints?: {
    coll: Address;
    debt: Address;
}[], repayWithCollObligation?: KaminoObligation | undefined, payer?: TransactionSigner) => Promise<[Address, Instruction[][]]>;
export declare function getAllUserMetadatasWithFilter(rpc: Rpc<GetProgramAccountsApi>, filter: (GetProgramAccountsDatasizeFilter | GetProgramAccountsMemcmpFilter)[], programId: Address): Promise<KaminoUserMetadata[]>;
//# sourceMappingURL=userMetadata.d.ts.map