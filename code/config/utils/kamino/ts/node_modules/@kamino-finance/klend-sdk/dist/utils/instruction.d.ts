import Decimal from 'decimal.js';
import { Address, Instruction, Rpc, GetMultipleAccountsApi, Account } from '@solana/kit';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
export declare function buildComputeBudgetIx(units: number): Instruction;
export declare function getLookupTableAccounts(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[]): Promise<Account<AddressLookupTable>[]>;
export declare const getComputeBudgetAndPriorityFeeIxs: (units: number, priorityFeeLamports?: Decimal) => Instruction[];
export declare function notEmpty<TValue>(value: TValue | null | undefined): value is TValue;
export declare function uniqueAccountsWithProgramIds(ixs: Instruction[], addressLookupTables?: Address[] | Account<AddressLookupTable>[]): Array<Address>;
export declare function removeBudgetIxs(ixs: Instruction[]): Instruction[];
//# sourceMappingURL=instruction.d.ts.map