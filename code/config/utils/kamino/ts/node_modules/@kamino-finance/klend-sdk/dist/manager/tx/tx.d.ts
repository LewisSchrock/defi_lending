import { Account, Blockhash, FullySignedTransaction, GetEpochInfoApi, GetLatestBlockhashApi, GetSignatureStatusesApi, Instruction, RpcSubscriptions, SendTransactionApi, Signature, SignatureNotificationsApi, SlotNotificationsApi, TransactionSigner, TransactionWithBlockhashLifetime } from '@solana/kit';
import { Rpc } from '@solana/kit';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
import { ManagerConnectionPool } from './ManagerConnectionPool';
export declare function sendAndConfirmTx(c: ManagerConnectionPool, payer: TransactionSigner, ixs: Instruction[], luts?: Account<AddressLookupTable>[]): Promise<Signature>;
export type BlockhashWithHeight = {
    blockhash: Blockhash;
    lastValidBlockHeight: bigint;
    slot: bigint;
};
export declare function fetchBlockhash(rpc: Rpc<GetLatestBlockhashApi>): Promise<BlockhashWithHeight>;
export declare function sendAndConfirmTxImpl({ rpc, wsRpc, }: {
    rpc: Rpc<GetEpochInfoApi & GetSignatureStatusesApi & SendTransactionApi>;
    wsRpc: RpcSubscriptions<SignatureNotificationsApi & SlotNotificationsApi>;
}, tx: FullySignedTransaction & TransactionWithBlockhashLifetime, slot: bigint): Promise<void>;
//# sourceMappingURL=tx.d.ts.map