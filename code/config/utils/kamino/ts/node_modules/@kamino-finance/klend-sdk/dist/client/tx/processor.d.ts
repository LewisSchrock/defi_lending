import { CliConnectionPool } from './CliConnectionPool';
import { Account, Instruction, TransactionSigner } from '@solana/kit';
import { SendTxMode } from './CliEnv';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
export declare function processTx(c: CliConnectionPool, payer: TransactionSigner, ixs: Instruction[], mode: SendTxMode, luts?: Account<AddressLookupTable>[]): Promise<void>;
//# sourceMappingURL=processor.d.ts.map