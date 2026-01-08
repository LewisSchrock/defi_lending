import { Address, GetProgramAccountsDatasizeFilter, GetProgramAccountsMemcmpFilter } from '@solana/kit';
import { CliConnectionPool } from '../tx/CliConnectionPool';
export declare function downloadUserMetadatasWithFilter(c: CliConnectionPool, filter: (GetProgramAccountsDatasizeFilter | GetProgramAccountsMemcmpFilter)[], output: string, programId: Address): Promise<void>;
//# sourceMappingURL=userMetadata.d.ts.map