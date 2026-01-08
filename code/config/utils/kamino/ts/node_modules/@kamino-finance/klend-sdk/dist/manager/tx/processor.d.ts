import { ManagerConnectionPool } from './ManagerConnectionPool';
import { Account, Instruction, TransactionSigner } from '@solana/kit';
import { SendTxMode } from './ManagerEnv';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
export declare function processTx(c: ManagerConnectionPool, payer: TransactionSigner, ixs: Instruction[], mode: SendTxMode, luts?: Account<AddressLookupTable>[]): Promise<void>;
//# sourceMappingURL=processor.d.ts.map