import { Address, GetAccountInfoApi, GetSlotApi, Instruction, Rpc, Slot, TransactionSigner } from '@solana/kit';
export declare function printAddressLookupTable(rpc: Rpc<GetAccountInfoApi>, lookupTablePk: Address): Promise<void>;
export declare function createLookupTableIx(connection: Rpc<GetSlotApi>, authority: TransactionSigner): Promise<[Instruction, Address]>;
export declare function extendLookupTableChunkIx(authority: TransactionSigner, lookupTablePk: Address, keys: Address[], payer?: TransactionSigner): Instruction;
export declare const extendLookupTableIxs: (authority: TransactionSigner, table: Address, keys: Address[], payer?: TransactionSigner) => Instruction[];
/**
 * This method returns an instruction that creates a lookup table, alongside the pubkey of the lookup table
 * @param authority - the owner of the lookup table
 * @param recentSlot - the current slot
 * @returns - the instruction to create the lookup table and its address
 */
export declare function initLookupTableIx(authority: TransactionSigner, recentSlot: Slot): Promise<[Instruction, Address]>;
/**
 * This method retuns an instruction that deactivates a lookup table, which is needed to close it
 * @param authority - the owner of the lookup table
 * @param lookupTable - the lookup table to deactivate
 * @returns - the instruction to deactivate the lookup table
 */
export declare function deactivateLookupTableIx(authority: TransactionSigner, lookupTable: Address): Instruction;
/**
 * This method returns an instruction that closes a lookup table. That lookup table needs to be disabled at least 500 blocks before closing it.
 * @param authority - the owner of the lookup table
 * @param lookupTable - the lookup table to close
 * @returns - the instruction to close the lookup table
 */
export declare function closeLookupTableIx(authority: TransactionSigner, lookupTable: Address): Instruction;
/**
 * Returns the accounts in a lookup table
 * @param rpc
 * @param lookupTable - lookup table to get the accounts from
 * @returns - an array of accounts in the lookup table or an empty array if the lookup table does not exist
 */
export declare function getAccountsInLut(rpc: Rpc<GetAccountInfoApi>, lookupTable: Address): Promise<Address[]>;
/**
 * This method inserts the missing keys from the provided keys into an existent lookup table
 * @param authority - payer wallet pubkey
 * @param lookupTable - lookup table to insert the keys into
 * @param keys - keys to insert into the lookup table
 * @param [accountsInLut] - the existent accounts in the lookup table. Optional. If provided, the function will not fetch the accounts in the lookup table
 * @returns - an array of instructions to insert the missing keys into the lookup table
 */
export declare function insertIntoLookupTableIxs(rpc: Rpc<GetAccountInfoApi>, authority: TransactionSigner, lookupTable: Address, keys: Address[], accountsInLut?: Address[]): Promise<Instruction[]>;
//# sourceMappingURL=lookupTable.d.ts.map