import { Account, Instruction, TransactionSigner } from '@solana/kit';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
export declare function printMultisigTx(payer: TransactionSigner, ixs: Instruction[], luts?: Account<AddressLookupTable>[]): Promise<void>;
//# sourceMappingURL=multisig.d.ts.map