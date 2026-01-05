import { Instruction, TransactionSigner, Account } from '@solana/kit';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
import { BlockhashWithHeight } from './tx';
import { CliConnectionPool } from './CliConnectionPool';
export declare const INVALID_BUT_SUFFICIENT_FOR_COMPILATION_BLOCKHASH: BlockhashWithHeight;
export declare function printSimulateTx(c: CliConnectionPool, payer: TransactionSigner, ixs: Instruction[], luts?: Account<AddressLookupTable>[]): Promise<void>;
//# sourceMappingURL=simulate.d.ts.map