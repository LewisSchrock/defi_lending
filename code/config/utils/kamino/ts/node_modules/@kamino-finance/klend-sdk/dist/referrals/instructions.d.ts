import { Address, Instruction, Rpc, SolanaRpcApi, TransactionSigner } from '@solana/kit';
import { KaminoMarket } from '../classes';
export declare const getInitAllReferrerTokenStateIxs: ({ payer, kaminoMarket, referrer, }: {
    payer: TransactionSigner;
    kaminoMarket: KaminoMarket;
    referrer?: Address;
}) => Promise<Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>[]>;
export declare const getInitReferrerStateAndShortUrlIxs: ({ referrer, shortUrl, programId, }: {
    referrer: TransactionSigner;
    shortUrl: string;
    programId: Address;
}) => Promise<Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>>;
export declare const getDeleteReferrerStateAndShortUrlIxs: ({ referrer, rpc, programId, }: {
    referrer: TransactionSigner;
    rpc: Rpc<SolanaRpcApi>;
    programId: Address;
}) => Promise<Instruction>;
//# sourceMappingURL=instructions.d.ts.map