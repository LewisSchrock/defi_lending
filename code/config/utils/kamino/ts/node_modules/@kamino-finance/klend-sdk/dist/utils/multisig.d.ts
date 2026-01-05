import { Address } from '@solana/kit';
export declare function walletIsSquadsMultisig(wallet: Address): Promise<boolean>;
export declare function getSquadsMultisigAdminsAndThreshold(wallet: Address): Promise<{
    adminsNumber: number;
    threshold: number;
}>;
export type SquadsMultisigResponse = {
    isSquad: boolean;
    version: string;
};
export interface WalletType {
    walletType: 'simpleWallet' | 'squadsMultisig';
    walletAdminsNumber: number;
    walletThreshold: number;
}
export type SquadsV4MultisigAccountResponse = {
    account: {
        bump: number;
        configAuthority: string;
        createKey: string;
        members: number[][];
        rentCollector: string;
        staleTransactionIndex: string;
        threshold: number;
        timeLock: number;
        total_signers: number;
        transactionIndex: string;
    };
    address: string;
    defaultVault: string;
    metadata: {
        version: string;
    };
};
export type SquadsV3MultisigAccountResponse = {
    allow_external_execute: boolean;
    authority_index: number;
    bump: number;
    create_key: string;
    keys: number[][];
    ms_change_index: number;
    threshold: number;
    transaction_index: number;
};
//# sourceMappingURL=multisig.d.ts.map