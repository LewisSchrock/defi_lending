import { Address, Option, TransactionSigner } from '@solana/kit';
import { KaminoReserve } from '../classes';
import Decimal from 'decimal.js';
export declare const getFlashLoanInstructions: (args: {
    borrowIxIndex: number;
    userTransferAuthority: TransactionSigner;
    lendingMarketAuthority: Address;
    lendingMarketAddress: Address;
    reserve: KaminoReserve;
    amountLamports: Decimal;
    destinationAta: Address;
    referrerAccount: Option<Address>;
    referrerTokenState: Option<Address>;
    programId: Address;
}) => {
    flashBorrowIx: import("@solana/kit").Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
    flashRepayIx: import("@solana/kit").Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
};
export declare const getBorrowFlashLoanInstruction: ({ userTransferAuthority, lendingMarketAuthority, lendingMarketAddress, reserve, amountLamports, destinationAta, referrerAccount, referrerTokenState, programId, }: {
    userTransferAuthority: TransactionSigner;
    lendingMarketAuthority: Address;
    lendingMarketAddress: Address;
    reserve: KaminoReserve;
    amountLamports: Decimal;
    destinationAta: Address;
    referrerAccount: Option<Address>;
    referrerTokenState: Option<Address>;
    programId: Address;
}) => import("@solana/kit").Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
export declare const getRepayFlashLoanInstruction: ({ borrowIxIndex, userTransferAuthority, lendingMarketAuthority, lendingMarketAddress, reserve, amountLamports, userSourceLiquidity, referrerAccount, referrerTokenState, programId, }: {
    borrowIxIndex: number;
    userTransferAuthority: TransactionSigner;
    lendingMarketAuthority: Address;
    lendingMarketAddress: Address;
    reserve: KaminoReserve;
    amountLamports: Decimal;
    userSourceLiquidity: Address;
    referrerAccount: Option<Address>;
    referrerTokenState: Option<Address>;
    programId: Address;
}) => import("@solana/kit").Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=instructions.d.ts.map